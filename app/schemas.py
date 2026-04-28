from datetime import date

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    email: str

    model_config = {"from_attributes": True}


# --- Cleaners ---

class CleanerBase(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None


class CleanerCreate(CleanerBase):
    pass


class CleanerResponse(CleanerBase):
    id: int

    model_config = {"from_attributes": True}


class CleanerWithBookings(CleanerResponse):
    bookings: list["BookingResponse"] = []

    model_config = {"from_attributes": True}


# --- Bookings ---

class BookingBase(BaseModel):
    confirmation_code: str
    status: str
    guest_name: str
    contact: str | None = None
    adults: int = 0
    children: int = 0
    infants: int = 0
    start_date: date
    end_date: date
    nights: int
    booked_date: date | None = None
    listing: str | None = None
    earnings: str | None = None
    cleaner_id: int | None = None


class BookingCreate(BookingBase):
    pass


class BookingResponse(BookingBase):
    id: int
    cleaner: CleanerResponse | None = None

    model_config = {"from_attributes": True}


CleanerWithBookings.model_rebuild()