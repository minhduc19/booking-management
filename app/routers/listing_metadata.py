from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/listing-metadata", tags=["listing-metadata"])


def _get_listing_metadata_or_404(
    metadata_id: int, db: Session
) -> models.ListingMetadata:
    listing_metadata = db.get(models.ListingMetadata, metadata_id)
    if listing_metadata is None:
        raise HTTPException(status_code=404, detail="Listing metadata not found")
    return listing_metadata


def _validate_property(property_id: int | None, db: Session) -> None:
    if property_id is not None and db.get(models.Property, property_id) is None:
        raise HTTPException(status_code=404, detail="Property not found")


def _commit_or_listing_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Listing already exists") from exc


@router.post(
    "/",
    response_model=schemas.ListingMetadataResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_listing_metadata(
    payload: schemas.ListingMetadataCreate, db: Session = Depends(get_db)
):
    _validate_property(payload.property_id, db)
    listing_metadata = models.ListingMetadata(**payload.model_dump())
    db.add(listing_metadata)
    _commit_or_listing_conflict(db)
    db.refresh(listing_metadata)
    return listing_metadata


@router.get("/", response_model=list[schemas.ListingMetadataResponse])
def list_listing_metadata(db: Session = Depends(get_db)):
    return db.query(models.ListingMetadata).order_by(models.ListingMetadata.id).all()


@router.get("/{metadata_id}", response_model=schemas.ListingMetadataResponse)
def get_listing_metadata(metadata_id: int, db: Session = Depends(get_db)):
    return _get_listing_metadata_or_404(metadata_id, db)


@router.patch("/{metadata_id}", response_model=schemas.ListingMetadataResponse)
def update_listing_metadata(
    metadata_id: int,
    payload: schemas.ListingMetadataUpdate,
    db: Session = Depends(get_db),
):
    listing_metadata = _get_listing_metadata_or_404(metadata_id, db)
    changes = payload.model_dump(exclude_unset=True)

    if "property_id" in changes:
        _validate_property(changes["property_id"], db)

    for field, value in changes.items():
        setattr(listing_metadata, field, value)

    _commit_or_listing_conflict(db)
    db.refresh(listing_metadata)
    return listing_metadata


@router.delete("/{metadata_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_listing_metadata(metadata_id: int, db: Session = Depends(get_db)):
    listing_metadata = _get_listing_metadata_or_404(metadata_id, db)
    db.delete(listing_metadata)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
