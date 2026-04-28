from sqlalchemy import Column, Date, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class Cleaner(Base):
    __tablename__ = "cleaners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    phone = Column(String, nullable=True)

    bookings = relationship("Booking", back_populates="cleaner")


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
    earnings = Column(String, nullable=True)  # stored as string to preserve currency symbol
    cleaner_id = Column(Integer, ForeignKey("cleaners.id"), nullable=True)

    cleaner = relationship("Cleaner", back_populates="bookings")