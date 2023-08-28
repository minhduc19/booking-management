from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.types import Text
from sqlalchemy.orm import relationship
from sqlalchemy.schema import PrimaryKeyConstraint
from sqlalchemy.orm import Mapped
from .database import Base
from typing import List
from sqlalchemy.orm.collections import MappedCollection


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)