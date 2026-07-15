import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])

LISTING_TO_NUMBER = {
    "Spacious cosy room with prime location": "Room 4 - 1419",
    "Spacious - central - historic view": "Room 3 - 1951",
    "Unique - spacious - central - with living space": "Room 1 - 1219",
    "Relaxing - good location - well furnished": "Room 2 - 1319",
    "Stylish, Walking Distance to Centre, Free Parking": "Room 1",
    "En-suite, Walking Distance to Centre, Free Parking": "Room 3",
    "Cosy, Walking Distance to Centre, Free Parking": "Room 2",
    "Unique oval room -Spacious -Central - Living Space": "Room 5 - 1519",
}

LISTING_TO_PROPERTY = {
    "Spacious cosy room with prime location": "2 Pilrig Street",
    "Spacious - central - historic view": "2 Pilrig Street",
    "Unique - spacious - central - with living space": "2 Pilrig Street",
    "Relaxing - good location - well furnished": "2 Pilrig Street",
    "Stylish, Walking Distance to Centre, Free Parking": "35 Pilrig Heights",
    "En-suite, Walking Distance to Centre, Free Parking": "35 Pilrig Heights",
    "Cosy, Walking Distance to Centre, Free Parking": "35 Pilrig Heights",
    "Unique oval room -Spacious -Central - Living Space": "2 Pilrig Street",
}

COLUMN_MAP = {
    "Confirmation code": "confirmation_code",
    "Status": "status",
    "Guest name": "guest_name",
    "Contact": "contact",
    "# of adults": "adults",
    "# of children": "children",
    "# of infants": "infants",
    "Start date": "start_date",
    "End date": "end_date",
    "# of nights": "nights",
    "Booked": "booked_date",
    "Listing": "listing",
    "Earnings": "earnings",
}


def parse_date(value: str):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date format: {value!r}")


@router.post("/", response_model=schemas.BookingResponse)
async def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    db_booking = models.Booking(**booking.model_dump())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


@router.get("/", response_model=list[schemas.BookingResponse])
async def list_bookings(db: Session = Depends(get_db)):
    return db.query(models.Booking).all()


@router.get("/{confirmation_code}", response_model=schemas.BookingResponse)
async def get_booking(confirmation_code: str, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(
        models.Booking.confirmation_code == confirmation_code
    ).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.delete("/{confirmation_code}")
async def delete_booking(confirmation_code: str, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(
        models.Booking.confirmation_code == confirmation_code
    ).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    deleted_session_bookings = db.query(models.SessionBooking).filter(
        models.SessionBooking.confirmation_code == confirmation_code
    ).delete(synchronize_session=False)

    db.delete(booking)
    db.commit()
    return {
        "deleted": confirmation_code,
        "deleted_session_bookings": deleted_session_bookings,
    }


@router.get("/checkout/")
async def bookings_by_checkout(db: Session = Depends(get_db)):
    bookings = (
        db.query(models.Booking)
        .options(
            joinedload(models.Booking.session_bookings)
            .joinedload(models.SessionBooking.session)
            .joinedload(models.CleaningSession.cleaner),
            joinedload(models.Booking.property),
        )
        .order_by(models.Booking.end_date)
        .all()
    )

    grouped: dict = {}

    for booking in bookings:
        date_key = str(booking.end_date)
        if date_key not in grouped:
            grouped[date_key] = {"total": 0, "by_property": {}, "unassigned": []}

        grouped[date_key]["total"] += 1

        sessions = [
            {
                "session_id": sb.session.id,
                "cleaner_id": sb.session.cleaner_id,
                "cleaner_name": sb.session.cleaner.name if sb.session.cleaner else None,
                "clean_date": sb.session.clean_date,
                "hours": sb.session.hours,
                "minutes": sb.session.minutes,
                "notes": sb.session.notes,
                "fix_cost": sb.session.fix_cost,
                "paid_status": sb.session.paid_status,
            }
            for sb in booking.session_bookings
            if sb.session
        ]

        seen = set()
        unique_sessions = []
        for s in sessions:
            if s["session_id"] not in seen:
                seen.add(s["session_id"])
                unique_sessions.append(s)

        entry = {
            "confirmation_code": booking.confirmation_code,
            "listing": booking.listing,
            "listing_number": booking.listing_number,
            "sessions": unique_sessions,
        }

        if booking.property:
            address = booking.property.address
            if address not in grouped[date_key]["by_property"]:
                grouped[date_key]["by_property"][address] = []
            grouped[date_key]["by_property"][address].append(entry)
        else:
            grouped[date_key]["unassigned"].append(entry)

    return [
        {
            "checkout_date": date_key,
            "total": data["total"],
            "by_property": [
                {"property": address, "count": len(entries), "bookings": entries}
                for address, entries in data["by_property"].items()
            ],
            "unassigned": data["unassigned"],
        }
        for date_key, data in grouped.items()
    ]


@router.post("/bulk-upload/")
async def bulk_upload_bookings(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    all_created, all_updated, all_errors = [], [], []

    async def process_file(file: UploadFile):
        created, updated, errors = [], [], []

        if not file.filename.endswith(".csv"):
            errors.append({"file": file.filename, "row": None, "error": "Not a CSV file"})
            return created, updated, errors

        contents = await file.read()
        reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))

        for i, row in enumerate(reader, start=2):
            try:
                data = {model_field: row[csv_col].strip() for csv_col, model_field in COLUMN_MAP.items()}

                data["adults"] = int(data["adults"])
                data["children"] = int(data["children"])
                data["infants"] = int(data["infants"])
                data["nights"] = int(data["nights"])
                data["start_date"] = parse_date(data["start_date"])
                data["end_date"] = parse_date(data["end_date"])
                data["booked_date"] = parse_date(data["booked_date"]) if data["booked_date"] else None

                listing = data.get("listing", "")
                data["listing_number"] = LISTING_TO_NUMBER.get(listing)

                property_address = LISTING_TO_PROPERTY.get(listing)
                if property_address:
                    prop = db.query(models.Property).filter(
                        models.Property.address == property_address
                    ).first()
                    if not prop:
                        prop = models.Property(address=property_address)
                        db.add(prop)
                        db.flush()
                    data["property_id"] = prop.id

                exists = db.query(models.Booking).filter(
                    models.Booking.confirmation_code == data["confirmation_code"]
                ).first()
                if exists:
                    for key, value in data.items():
                        setattr(exists, key, value)
                    updated.append(data["confirmation_code"])
                else:
                    db.add(models.Booking(**data))
                    created.append(data["confirmation_code"])

            except Exception as e:
                errors.append({"file": file.filename, "row": i, "error": str(e)})

        return created, updated, errors

    for file in files:
        created, updated, errors = await process_file(file)
        all_created.extend(created)
        all_updated.extend(updated)
        all_errors.extend(errors)

    db.commit()

    return {
        "files_processed": len(files),
        "created": len(all_created),
        "updated": len(all_updated),
        "errors": all_errors,
        "created_codes": all_created,
        "updated_codes": all_updated,
    }
