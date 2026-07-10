from app import models
from .database import client, session


def _create_booking(client, confirmation_code="CONF-DELETE"):
    payload = {
        "confirmation_code": confirmation_code,
        "status": "confirmed",
        "guest_name": "Delete Test Guest",
        "start_date": "2026-05-10",
        "end_date": "2026-05-12",
        "nights": 2,
    }
    response = client.post("/bookings/", json=payload)
    assert response.status_code == 200
    return response.json()


def test_delete_booking_removes_booking_and_session_links(client, session):
    _create_booking(client)
    cleaner_response = client.post("/cleaners/", json={"name": "Delete Test Cleaner"})
    assert cleaner_response.status_code == 200

    session_response = client.post(
        "/cleaning-sessions/",
        json={
            "cleaner_id": cleaner_response.json()["id"],
            "clean_date": "2026-05-12",
            "hours": 1,
            "minutes": 30,
            "confirmation_codes": ["CONF-DELETE"],
        },
    )
    assert session_response.status_code == 200
    assert session.query(models.SessionBooking).count() == 1

    response = client.delete("/bookings/CONF-DELETE")

    assert response.status_code == 200
    assert response.json() == {
        "deleted": "CONF-DELETE",
        "deleted_session_bookings": 1,
    }
    assert session.query(models.Booking).filter_by(confirmation_code="CONF-DELETE").first() is None
    assert session.query(models.SessionBooking).count() == 0


def test_delete_booking_returns_404_for_unknown_confirmation_code(client):
    response = client.delete("/bookings/DOES-NOT-EXIST")

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking not found"}
