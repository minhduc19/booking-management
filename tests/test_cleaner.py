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
    assert created.status_code == 200
    assert created.json()["paid_status"] is False
    session_id = created.json()["id"]

    update_payload = {
        "hours": 3,
        "minutes": 45,
        "notes": "Updated session",
        "fix_cost": 42.5,
        "paid_status": True,
    }
    updated = client.patch(f"/cleaning-sessions/{session_id}", json=update_payload)

    assert updated.status_code == 200
    assert updated.json()["hours"] == 3
    assert updated.json()["minutes"] == 45
    assert updated.json()["notes"] == "Updated session"
    assert updated.json()["fix_cost"] == 42.5
    assert updated.json()["paid_status"] is True
    assert len(updated.json()["session_bookings"]) == 1

    fetched = client.get(f"/cleaning-sessions/{session_id}")
    assert fetched.status_code == 200
    assert fetched.json()["paid_status"] is True

    listed = client.get("/cleaning-sessions/")
    assert listed.status_code == 200
    assert listed.json()[0]["paid_status"] is True

    cleaner_sessions = client.get(f"/cleaners/{cleaner_id}/sessions")
    assert cleaner_sessions.status_code == 200
    assert cleaner_sessions.json()["sessions"][0]["paid_status"] is True

    checkout = client.get("/bookings/checkout/")
    assert checkout.status_code == 200
    checkout_session = checkout.json()[0]["unassigned"][0]["sessions"][0]
    assert checkout_session["cleaner_id"] == cleaner_id
    assert checkout_session["paid_status"] is True
