import csv
import io
from datetime import date, datetime

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional
from app import models, schemas
from app.database import engine, get_db
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse



models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/index-checkout", response_class=HTMLResponse)
async def read_index():
    with open("frontend/checkout.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/index-upload", response_class=HTMLResponse)
async def read_upload():
    with open("frontend/upload.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/index-cleaner", response_class=HTMLResponse)
async def read_cleaner():
    with open("frontend/cleaner.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/")
def read_root():
    return {"message": "Changed to private repository"}


# --- Users ---

@app.post("/users/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = user.password  # Replace with bcrypt in production
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user



# --- Cleaners ---

@app.post("/cleaners/", response_model=schemas.CleanerResponse)
def create_cleaner(cleaner: schemas.CleanerCreate, db: Session = Depends(get_db)):
    db_cleaner = models.Cleaner(**cleaner.model_dump())
    db.add(db_cleaner)
    db.commit()
    db.refresh(db_cleaner)
    return db_cleaner


@app.get("/cleaners/", response_model=list[schemas.CleanerResponse])
def list_cleaners(db: Session = Depends(get_db)):
    return db.query(models.Cleaner).all()


@app.get("/cleaners/{cleaner_id}", response_model=schemas.CleanerResponse)
def get_cleaner(cleaner_id: int, db: Session = Depends(get_db)):
    cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == cleaner_id).first()
    if cleaner is None:
        raise HTTPException(status_code=404, detail="Cleaner not found")
    return cleaner




@app.get(
    "/cleaners/{cleaner_id}/sessions",
    response_model=schemas.CleanerResponse
)
def get_cleaner_sessions(
    cleaner_id: int,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db)
):
    cleaner = db.query(models.Cleaner).filter(
        models.Cleaner.id == cleaner_id
    ).first()

    if cleaner is None:
        raise HTTPException(
            status_code=404,
            detail="Cleaner not found"
        )

    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=400,
            detail="start_date cannot be greater than end_date"
        )

    query = db.query(models.CleaningSession).filter(
        models.CleaningSession.cleaner_id == cleaner_id
    )

    if start_date:
        query = query.filter(
            models.CleaningSession.clean_date >= start_date
        )

    if end_date:
        query = query.filter(
            models.CleaningSession.clean_date <= end_date
        )

    filtered_sessions = query.order_by(
        models.CleaningSession.clean_date.asc()
    ).all()

    # Replace cleaner.sessions with filtered result
    cleaner.sessions = filtered_sessions

    return cleaner

# --- Bookings ---

@app.post("/bookings/", response_model=schemas.BookingResponse)
def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    db_booking = models.Booking(**booking.model_dump())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking


@app.get("/bookings/", response_model=list[schemas.BookingResponse])
def list_bookings(db: Session = Depends(get_db)):
    return db.query(models.Booking).all()


@app.get("/bookings/{confirmation_code}", response_model=schemas.BookingResponse)
def get_booking(confirmation_code: str, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(
        models.Booking.confirmation_code == confirmation_code
    ).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking



@app.delete("/bookings/")
def delete_all_bookings(db: Session = Depends(get_db)):
    deleted = db.query(models.Booking).delete()
    db.commit()
    return {"deleted": deleted}



@app.get("/bookings/checkout/")
def bookings_by_checkout(db: Session = Depends(get_db)):
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
                "cleaner_name": sb.session.cleaner.name if sb.session.cleaner else None,
            }
            for sb in booking.session_bookings
            if sb.session
        ]

        # Deduplicate by session_id
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

# --- Bulk CSV Upload ---

LISTING_TO_NUMBER = {
    "Spacious cosy room with prime location": "4",
    "Spacious - central - historic view": "3",
    "Unique - spacious - central - with living space": "1",
    "Relaxing - good location - well furnished": "2",
    "Stylish, Walking Distance to Centre, Free Parking": "1",
    "En-suite, Walking Distance to Centre, Free Parking": "3",
    "Cosy, Walking Distance to Centre, Free Parking": "2",
}

LISTING_TO_PROPERTY = {
    "Spacious cosy room with prime location": "2 Pilrig Street",
    "Spacious - central - historic view": "2 Pilrig Street",
    "Unique - spacious - central - with living space": "2 Pilrig Street",
    "Relaxing - good location - well furnished": "2 Pilrig Street",
    "Stylish, Walking Distance to Centre, Free Parking": "35 Pilrig Heights",
    "En-suite, Walking Distance to Centre, Free Parking": "35 Pilrig Heights",
    "Cosy, Walking Distance to Centre, Free Parking": "35 Pilrig Heights",
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

@app.post("/bookings/bulk-upload/")
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
 
                # Type coercions
                data["adults"] = int(data["adults"])
                data["children"] = int(data["children"])
                data["infants"] = int(data["infants"])
                data["nights"] = int(data["nights"])
                data["start_date"] = parse_date(data["start_date"])
                data["end_date"] = parse_date(data["end_date"])
                data["booked_date"] = parse_date(data["booked_date"]) if data["booked_date"] else None
 
                # Resolve listing metadata
                listing = data.get("listing", "")
                data["listing_number"] = LISTING_TO_NUMBER.get(listing)

                # Resolve property from listing name
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
 
                # Upsert — update if exists, create if not
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



# --- Cleaning Sessions ---

@app.post("/cleaning-sessions/", response_model=schemas.CleaningSessionResponse)
def create_cleaning_session(session: schemas.CleaningSessionCreate, db: Session = Depends(get_db)):
    if not 0 <= session.minutes <= 59:
        raise HTTPException(status_code=400, detail="minutes must be between 0 and 59")
    cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == session.cleaner_id).first()
    if cleaner is None:
        raise HTTPException(status_code=404, detail="Cleaner not found")

    # Validate all confirmation codes exist
    for code in session.confirmation_codes:
        if not db.query(models.Booking).filter(models.Booking.confirmation_code == code).first():
            raise HTTPException(status_code=404, detail=f"Booking not found: {code}")

    data = session.model_dump(exclude={"confirmation_codes"})
    db_session = models.CleaningSession(**data)
    db.add(db_session)
    db.commit()                   # ← guarantees id is written to DB
    db.refresh(db_session)        # ← populates db_session.id

    for code in session.confirmation_codes:
        db.add(models.SessionBooking(session_id=db_session.id, confirmation_code=code))

    db.commit()
    db.refresh(db_session)
    return db_session


@app.post("/cleaning-sessions/{session_id}/add-booking/{confirmation_code}", response_model=schemas.CleaningSessionResponse)
def add_booking_to_session(session_id: int, confirmation_code: str, db: Session = Depends(get_db)):
    session = db.query(models.CleaningSession).filter(models.CleaningSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not db.query(models.Booking).filter(models.Booking.confirmation_code == confirmation_code).first():
        raise HTTPException(status_code=404, detail="Booking not found")
    already = db.query(models.SessionBooking).filter(
        models.SessionBooking.session_id == session_id,
        models.SessionBooking.confirmation_code == confirmation_code
    ).first()
    if already:
        raise HTTPException(status_code=400, detail="Booking already in this session")
    db.add(models.SessionBooking(session_id=session_id, confirmation_code=confirmation_code))
    db.commit()
    db.refresh(session)
    return session


@app.get("/cleaning-sessions/", response_model=list[schemas.CleaningSessionResponse])
def list_cleaning_sessions(cleaner_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.CleaningSession)
    if cleaner_id:
        query = query.filter(models.CleaningSession.cleaner_id == cleaner_id)
    return query.all()


@app.get("/cleaning-sessions/{session_id}", response_model=schemas.CleaningSessionResponse)
def get_cleaning_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.CleaningSession).filter(models.CleaningSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/cleaning-sessions/{session_id}")
def delete_cleaning_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.CleaningSession).filter(models.CleaningSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"deleted": session_id}