from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    email: str
    class Config:
        orm_mode = True
        from_attributes=True

class UserCreate(UserBase):
    hashed_password: str