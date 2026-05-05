from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class Property(Base):
    __tablename__ = "properties"

    id      = Column(Integer, primary_key=True, index=True)
    address = Column(String, unique=True, nullable=False)

    bookings = relationship("Booking", back_populates="property")


class Cleaner(Base):
    __tablename__ = "cleaners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)

    sessions = relationship("CleaningSession", back_populates="cleaner")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    confirmation_code = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False)
    guest_name = Column(String, nullable=False)
    contact = Column(String, nullable=True)
    adults = Column(Integer, default=0)
    children = Column(Integer, default=0)
    infants = Column(Integer, default=0)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    nights = Column(Integer, nullable=False)
    booked_date = Column(Date, nullable=True)
    listing = Column(String, nullable=True)
    earnings = Column(String, nullable=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=True)

    property = relationship("Property", back_populates="bookings")
    session_bookings = relationship("SessionBooking", back_populates="booking")


class CleaningSession(Base):
    __tablename__ = "cleaning_sessions"

    id         = Column(Integer, primary_key=True, index=True)
    cleaner_id = Column(Integer, ForeignKey("cleaners.id"), nullable=False)
    clean_date = Column(Date, nullable=False)
    hours      = Column(Integer, nullable=False, default=0)
    minutes    = Column(Integer, nullable=False, default=0)  # 0-59
    notes      = Column(String, nullable=True)

    cleaner          = relationship("Cleaner", back_populates="sessions")
    session_bookings = relationship("SessionBooking", back_populates="session")


class SessionBooking(Base):
    """Link table — one cleaning session can cover multiple bookings."""
    __tablename__ = "session_bookings"

    id                = Column(Integer, primary_key=True, index=True)
    session_id        = Column(Integer, ForeignKey("cleaning_sessions.id"), nullable=False)
    confirmation_code = Column(String, ForeignKey("bookings.confirmation_code"), nullable=False)

    session = relationship("CleaningSession", back_populates="session_bookings")
    booking = relationship("Booking", back_populates="session_bookings")