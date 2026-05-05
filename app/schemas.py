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


# --- Properties ---

class PropertyResponse(BaseModel):
    id: int
    address: str

    model_config = {"from_attributes": True}


# --- Cleaners ---

class CleanerBase(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    rate: float | None = None  # hourly rate


class CleanerCreate(CleanerBase):
    pass


class CleanerResponse(CleanerBase):
    id: int
    sessions: list["CleaningSessionResponse"] = []

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
    property_id: int | None = None


class BookingCreate(BookingBase):
    pass


class BookingResponse(BookingBase):
    id: int
    property: PropertyResponse | None = None

    model_config = {"from_attributes": True}




# --- Cleaning Sessions ---

class CleaningSessionCreate(BaseModel):
    cleaner_id: int
    clean_date: date
    hours: int = 0
    minutes: int = 0  # 0-59
    notes: str | None = None
    confirmation_codes: list[str] = []  # bookings to attach to this session


class SessionBookingResponse(BaseModel):
    id: int
    confirmation_code: str

    model_config = {"from_attributes": True}


class CleaningSessionResponse(BaseModel):
    id: int
    cleaner_id: int
    clean_date: date
    hours: int
    minutes: int
    notes: str | None = None
    cleaner: "CleanerResponse | None" = None
    #session_bookings: list[SessionBookingResponse] = []
 
    model_config = {"from_attributes": True}

CleanerResponse.model_rebuild()