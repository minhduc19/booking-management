from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/cleaning-sessions", tags=["cleaning-sessions"])


@router.post("/", response_model=schemas.CleaningSessionResponse)
async def create_cleaning_session(session: schemas.CleaningSessionCreate, db: Session = Depends(get_db)):
    if not 0 <= session.minutes <= 59:
        raise HTTPException(status_code=400, detail="minutes must be between 0 and 59")
    cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == session.cleaner_id).first()
    if cleaner is None:
        raise HTTPException(status_code=404, detail="Cleaner not found")

    for code in session.confirmation_codes:
        if not db.query(models.Booking).filter(models.Booking.confirmation_code == code).first():
            raise HTTPException(status_code=404, detail=f"Booking not found: {code}")

    data = session.model_dump(exclude={"confirmation_codes"})
    db_session = models.CleaningSession(**data)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    for code in session.confirmation_codes:
        db.add(models.SessionBooking(session_id=db_session.id, confirmation_code=code))

    db.commit()
    db.refresh(db_session)
    return db_session


@router.patch("/{session_id}", response_model=schemas.CleaningSessionResponse)
async def update_cleaning_session(session_id: int, payload: schemas.CleaningSessionUpdate, db: Session = Depends(get_db)):
    session = db.query(models.CleaningSession).filter(models.CleaningSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    data = payload.model_dump(exclude_unset=True)

    if "minutes" in data and not 0 <= data["minutes"] <= 59:
        raise HTTPException(status_code=400, detail="minutes must be between 0 and 59")

    if "cleaner_id" in data:
        cleaner = db.query(models.Cleaner).filter(models.Cleaner.id == data["cleaner_id"]).first()
        if cleaner is None:
            raise HTTPException(status_code=404, detail="Cleaner not found")

    if "confirmation_codes" in data:
        codes = data.pop("confirmation_codes")
        for code in codes:
            if not db.query(models.Booking).filter(models.Booking.confirmation_code == code).first():
                raise HTTPException(status_code=404, detail=f"Booking not found: {code}")

        db.query(models.SessionBooking).filter(models.SessionBooking.session_id == session_id).delete(synchronize_session=False)
        for code in codes:
            db.add(models.SessionBooking(session_id=session_id, confirmation_code=code))

    for key, value in data.items():
        setattr(session, key, value)

    db.commit()
    db.refresh(session)
    return session


@router.post("/{session_id}/add-booking/{confirmation_code}", response_model=schemas.CleaningSessionResponse)
async def add_booking_to_session(session_id: int, confirmation_code: str, db: Session = Depends(get_db)):
    session = db.query(models.CleaningSession).filter(models.CleaningSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not db.query(models.Booking).filter(models.Booking.confirmation_code == confirmation_code).first():
        raise HTTPException(status_code=404, detail="Booking not found")
    already = db.query(models.SessionBooking).filter(
        models.SessionBooking.session_id == session_id,
        models.SessionBooking.confirmation_code == confirmation_code,
    ).first()
    if already:
        raise HTTPException(status_code=400, detail="Booking already in this session")
    db.add(models.SessionBooking(session_id=session_id, confirmation_code=confirmation_code))
    db.commit()
    db.refresh(session)
    return session


@router.delete("/")
async def delete_cleaning_sessions_by_confirmation_codes(
    payload: schemas.CleaningSessionDeleteByCodes,
    db: Session = Depends(get_db),
):
    confirmation_codes = [code for code in payload.confirmation_codes if code]
    if not confirmation_codes:
        raise HTTPException(status_code=400, detail="confirmation_codes is required")

    session_ids = [
        session_id
        for (session_id,) in db.query(models.SessionBooking.session_id)
        .filter(models.SessionBooking.confirmation_code.in_(confirmation_codes))
        .distinct()
        .all()
    ]

    if not session_ids:
        return {"deleted_sessions": 0, "deleted_session_ids": [], "matched_confirmation_codes": confirmation_codes}

    sessions_to_delete = (
        db.query(models.CleaningSession)
        .filter(models.CleaningSession.id.in_(session_ids))
        .all()
    )

    for session in sessions_to_delete:
        db.delete(session)

    db.commit()

    return {
        "deleted_sessions": len(sessions_to_delete),
        "deleted_session_ids": session_ids,
        "matched_confirmation_codes": confirmation_codes,
    }


@router.get("/", response_model=list[schemas.CleaningSessionResponse])
async def list_cleaning_sessions(cleaner_id: int | None = None, db: Session = Depends(get_db)):
    query = db.query(models.CleaningSession)
    if cleaner_id:
        query = query.filter(models.CleaningSession.cleaner_id == cleaner_id)
    return query.all()


@router.get("/{session_id}", response_model=schemas.CleaningSessionResponse)
async def get_cleaning_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.CleaningSession).filter(models.CleaningSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def delete_cleaning_session(session_id: int, db: Session = Depends(get_db)):
    session = db.query(models.CleaningSession).filter(models.CleaningSession.id == session_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()
    return {"deleted": session_id}
