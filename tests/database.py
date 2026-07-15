from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import models
from app.main import app
from app.database import get_db, Base

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def seed_listing_metadata(db):
    metadata_rows = (
        ("Spacious cosy room with prime location", "Room 4 - 1419", "2 Pilrig Street"),
        ("Spacious - central - historic view", "Room 3 - 1951", "2 Pilrig Street"),
        (
            "Unique - spacious - central - with living space",
            "Room 1 - 1219",
            "2 Pilrig Street",
        ),
        (
            "Relaxing - good location - well furnished",
            "Room 2 - 1319",
            "2 Pilrig Street",
        ),
        (
            "Stylish, Walking Distance to Centre, Free Parking",
            "Room 1",
            "35 Pilrig Heights",
        ),
        (
            "En-suite, Walking Distance to Centre, Free Parking",
            "Room 3",
            "35 Pilrig Heights",
        ),
        (
            "Cosy, Walking Distance to Centre, Free Parking",
            "Room 2",
            "35 Pilrig Heights",
        ),
        (
            "Unique oval room -Spacious -Central - Living Space",
            "Room 5 - 1519",
            "2 Pilrig Street",
        ),
    )

    properties = {}
    for _, _, address in metadata_rows:
        if address not in properties:
            prop = models.Property(address=address)
            db.add(prop)
            db.flush()
            properties[address] = prop

    for listing, listing_number, address in metadata_rows:
        db.add(
            models.ListingMetadata(
                listing=listing,
                listing_number=listing_number,
                property_id=properties[address].id,
            )
        )
    db.commit()


@pytest.fixture()
def session():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    seed_listing_metadata(db)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(session):
    def override_get_db():
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
