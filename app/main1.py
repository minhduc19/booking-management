import csv
import io
from datetime import datetime

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

import models
import schemas
from database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


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


@app.get("/cleaners/{cleaner_id}", response_model=schemas.CleanerWithBookings)
def get_cleaner(cleaner_id: int, db: Session = Depends(get_db)):
    cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == cleaner_id).first()
    if cleaner is None:
        raise HTTPException(status_code=404, detail="Cleaner not found")
    return cleaner


@app.patch("/bookings/{confirmation_code}/assign-cleaner/{cleaner_id}", response_model=schemas.BookingResponse)
def assign_cleaner(confirmation_code: str, cleaner_id: int, db: Session = Depends(get_db)):
    booking = db.query(models.Booking).filter(models.Booking.confirmation_code == confirmation_code).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == cleaner_id).first()
    if cleaner is None:
        raise HTTPException(status_code=404, detail="Cleaner not found")
    booking.cleaner_id = cleaner_id
    db.commit()
    db.refresh(booking)
    return booking


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

# --- Bulk CSV Upload ---

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
async def bulk_upload_bookings(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted")

    contents = await file.read()
    reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))

    created, updated, errors = [], [], []

    for i, row in enumerate(reader, start=2):  # start=2 accounts for header row
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
            errors.append({"row": i, "error": str(e)})

    db.commit()

    return {
        "created": len(created),
        "updated": len(updated),
        "errors": errors,
        "created_codes": created,
        "updated_codes": updated,
    }