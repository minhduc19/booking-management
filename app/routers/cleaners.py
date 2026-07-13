from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/cleaners", tags=["cleaners"])


@router.post("/", response_model=schemas.CleanerResponse)
def create_cleaner(cleaner: schemas.CleanerCreate, db: Session = Depends(get_db)):
    db_cleaner = models.Cleaner(**cleaner.model_dump())
    db.add(db_cleaner)
    db.commit()
    db.refresh(db_cleaner)
    return db_cleaner


@router.get("/", response_model=list[schemas.CleanerResponse])
def list_cleaners(db: Session = Depends(get_db)):
    return db.query(models.Cleaner).all()


@router.get("/{cleaner_id}", response_model=schemas.CleanerResponse)
def get_cleaner(cleaner_id: int, db: Session = Depends(get_db)):
    cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == cleaner_id).first()
    if cleaner is None:
        raise HTTPException(status_code=404, detail="Cleaner not found")
    return cleaner


@router.get("/{cleaner_id}/sessions", response_model=schemas.CleanerResponse)
def get_cleaner_sessions(
    cleaner_id: int,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    db: Session = Depends(get_db),
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

    cleaner.sessions = filtered_sessions

    return cleaner
