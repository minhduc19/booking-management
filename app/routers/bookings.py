import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])

COLUMN_MAP = {
    "confirmation_code": ("Confirmation code", "Confirmation Code"),
    "status": ("Status", "Type"),
    "guest_name": ("Guest name", "Guest"),
    "contact": ("Contact",),
    "adults": ("# of adults",),
    "children": ("# of children",),
    "infants": ("# of infants",),
    "start_date": ("Start date",),
    "end_date": ("End date",),
    "nights": ("# of nights", "Nights"),
    "booked_date": ("Booked", "Booking date"),
    "listing": ("Listing",),
    "earnings": ("Earnings", "Gross earnings"),
}

OPTIONAL_FIELD_DEFAULTS = {
    "contact": "",
    "adults": "0",
    "children": "0",
    "infants": "0",
    "earnings": "",
}

DEFAULT_DATE_FORMATS = ("%d/%m/%Y", "%Y-%m-%d")
US_DATE_FORMATS = ("%m/%d/%Y", "%Y-%m-%d")


def parse_date(value: str, formats: tuple[str, ...] = DEFAULT_DATE_FORMATS):
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date format: {value!r}")


def get_date_formats(rows: list[dict[str, str]]) -> tuple[str, ...]:
    """Choose a date order for a CSV from dates that are not ambiguous."""
    date_columns = ("Date", "Booking date", "Start date", "End date")

    for row in rows:
        for column in date_columns:
            value = row.get(column, "").strip()
            try:
                month_or_day, day_or_month, _ = value.split("/")
                first = int(month_or_day)
                second = int(day_or_month)
            except ValueError:
                continue

            if first > 12 and second <= 12:
                return DEFAULT_DATE_FORMATS
            if second > 12 and first <= 12:
                return US_DATE_FORMATS

    return DEFAULT_DATE_FORMATS


def get_csv_value(row: dict[str, str], field: str) -> str:
    for column in COLUMN_MAP[field]:
        value = row.get(column)
        if value is not None:
            return value.strip()

    if field in OPTIONAL_FIELD_DEFAULTS:
        return OPTIONAL_FIELD_DEFAULTS[field]

    columns = ", ".join(COLUMN_MAP[field])
    raise ValueError(f"Missing required column for {field}: {columns}")


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
        .filter(func.lower(models.Booking.status).notin_(["cancelled", "canceled"]))
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


@router.get("/{confirmation_code}", response_model=schemas.BookingResponse)
def get_booking(confirmation_code: str, db: Session = Depends(get_db)):
    booking = (
        db.query(models.Booking)
        .filter(models.Booking.confirmation_code == confirmation_code)
        .first()
    )
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.delete("/{confirmation_code}")
def delete_booking(confirmation_code: str, db: Session = Depends(get_db)):
    booking = (
        db.query(models.Booking)
        .filter(models.Booking.confirmation_code == confirmation_code)
        .first()
    )
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")

    deleted_session_bookings = (
        db.query(models.SessionBooking)
        .filter(models.SessionBooking.confirmation_code == confirmation_code)
        .delete(synchronize_session=False)
    )

    db.delete(booking)
    db.commit()
    return {
        "deleted": confirmation_code,
        "deleted_session_bookings": deleted_session_bookings,
    }


@router.post("/bulk-upload/")
async def bulk_upload_bookings(
    files: list[UploadFile] = File(...), db: Session = Depends(get_db)
):
    all_created, all_updated, all_errors = [], [], []
    pending_bookings: dict[str, models.Booking] = {}
    created_confirmation_codes: set[str] = set()
    updated_confirmation_codes: set[str] = set()

    async def process_file(file: UploadFile):
        created, updated, errors = [], [], []

        if not file.filename.endswith(".csv"):
            errors.append(
                {"file": file.filename, "row": None, "error": "Not a CSV file"}
            )
            return created, updated, errors

        contents = await file.read()
        reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))
        rows = list(reader)
        date_formats = get_date_formats(rows)

        for i, row in enumerate(rows, start=2):
            try:
                data = {field: get_csv_value(row, field) for field in COLUMN_MAP}

                data["adults"] = int(data["adults"])
                data["children"] = int(data["children"])
                data["infants"] = int(data["infants"])
                data["nights"] = int(data["nights"])
                data["start_date"] = parse_date(data["start_date"], date_formats)
                data["end_date"] = parse_date(data["end_date"], date_formats)
                data["booked_date"] = (
                    parse_date(data["booked_date"], date_formats)
                    if data["booked_date"]
                    else None
                )

                listing = data.get("listing", "")
                listing_metadata = (
                    db.query(models.ListingMetadata)
                    .filter(models.ListingMetadata.listing == listing)
                    .first()
                )
                if listing_metadata:
                    data["listing_number"] = listing_metadata.listing_number
                    data["property_id"] = listing_metadata.property_id

                confirmation_code = data["confirmation_code"]
                exists = pending_bookings.get(confirmation_code)
                if exists is None:
                    exists = (
                        db.query(models.Booking)
                        .filter(
                            models.Booking.confirmation_code == confirmation_code
                        )
                        .first()
                    )
                if exists:
                    for key, value in data.items():
                        setattr(exists, key, value)
                    if (
                        confirmation_code not in created_confirmation_codes
                        and confirmation_code not in updated_confirmation_codes
                    ):
                        updated.append(confirmation_code)
                        updated_confirmation_codes.add(confirmation_code)
                else:
                    booking = models.Booking(**data)
                    db.add(booking)
                    pending_bookings[confirmation_code] = booking
                    created.append(confirmation_code)
                    created_confirmation_codes.add(confirmation_code)

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
