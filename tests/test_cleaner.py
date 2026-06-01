from app.main import app
from .database import client, session
from app import schemas


def test_root(client):
    res = client.get("/")
    print(res.json().get('message'))
    assert res.json().get('message') == 'Changed to private repository'
    assert res.status_code == 200


def test_create_cleaner(client):
    payload = {
        "name": "Maria",
        "email": "maria@example.com",
        "phone": "+44 7700 900000"
    }
    res = client.post("/cleaners/", json=payload)
    cleaner = schemas.CleanerResponse(**res.json())

    assert res.status_code == 200
    assert cleaner.name == "Maria"
    assert cleaner.email == "maria@example.com"
    assert cleaner.phone == "+44 7700 900000"


def test_create_cleaner_minimal(client):
    """Only name is required — email and phone are optional."""
    res = client.post("/cleaners/", json={"name": "John"})

    assert res.status_code == 200
    assert res.json()["name"] == "John"
    assert res.json()["email"] is None
    assert res.json()["phone"] is None

def test_update_cleaning_session(client):
    cleaner_res = client.post("/cleaners/", json={"name": "Session Cleaner"})
    cleaner_id = cleaner_res.json()["id"]

    booking_payload = {
        "confirmation_code": "CONF-100",
        "status": "confirmed",
        "guest_name": "Guest A",
        "start_date": "2026-05-10",
        "end_date": "2026-05-12",
        "nights": 2,
    }
    client.post("/bookings/", json=booking_payload)

    create_payload = {
        "cleaner_id": cleaner_id,
        "clean_date": "2026-05-12",
        "hours": 2,
        "minutes": 30,
        "notes": "Initial session",
        "fix_cost": 25.0,
        "confirmation_codes": ["CONF-100"],
    }
    created = client.post("/cleaning-sessions/", json=create_payload)
    session_id = created.json()["id"]

    update_payload = {
        "hours": 3,
        "minutes": 45,
        "notes": "Updated session",
        "fix_cost": 42.5,
    }
    updated = client.patch(f"/cleaning-sessions/{session_id}", json=update_payload)

    assert updated.status_code == 200
    assert updated.json()["hours"] == 3
    assert updated.json()["minutes"] == 45
    assert updated.json()["notes"] == "Updated session"
    assert updated.json()["fix_cost"] == 42.5
    assert len(updated.json()["session_bookings"]) == 1
