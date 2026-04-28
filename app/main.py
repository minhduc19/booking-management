from typing import Union

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.dialects import postgresql
from models import User
#import models,schemas
# from .database import SessionLocal, engine, get_db

# models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message":"Changed to private repository"}


# @app.post("/users/", response_model=schemas.UserCreate)
# def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
#     fake_hashed_password = user.hashed_password
#     db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
#     db.add(db_user)
#     db.commit()
#     db.refresh(db_user)
#     return db_user