from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import hash_password

router = APIRouter(prefix="/users", tags=["users"])


def _get_user_or_404(user_id: int, db: Session) -> models.User:
    user = db.get(models.User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def _commit_or_email_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered") from exc


@router.post("/", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = models.User(
        email=str(payload.email), hashed_password=hash_password(payload.password)
    )
    db.add(user)
    _commit_or_email_conflict(db)
    db.refresh(user)
    return user


@router.get("/", response_model=list[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.id).all()


@router.get("/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return _get_user_or_404(user_id, db)


@router.patch("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db)
):
    user = _get_user_or_404(user_id, db)
    changes = payload.model_dump(exclude_unset=True)
    if "email" in changes:
        if changes["email"] is None:
            raise HTTPException(status_code=422, detail="Email cannot be null")
        user.email = str(changes["email"])
    if "password" in changes:
        if changes["password"] is None:
            raise HTTPException(status_code=422, detail="Password cannot be null")
        user.hashed_password = hash_password(changes["password"])

    _commit_or_email_conflict(db)
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = _get_user_or_404(user_id, db)
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
