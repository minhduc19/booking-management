from app import models
from .database import client, session


def _booking_payload(confirmation_code="CONF-DELETE", **overrides):
    payload = {
        "confirmation_code": confirmation_code,
        "status": "confirmed",
        "guest_name": "Test Guest",
        "start_date": "2026-05-10",
        "end_date": "2026-05-12",
        "nights": 2,
    }
    payload.update(overrides)
    return payload


def _create_booking(client, confirmation_code="CONF-DELETE", **overrides):
    response = client.post(
        "/bookings/",
        json=_booking_payload(confirmation_code, **overrides),
    )
    assert response.status_code == 200
    return response.json()


def test_create_booking_persists_required_and_optional_fields(client, session):
    response = client.post(
        "/bookings/",
        json=_booking_payload(
            "CONF-CREATE",
            guest_name="Create Test Guest",
            contact="guest@example.com",
            adults=2,
            children=1,
            infants=1,
            booked_date="2026-04-01",
            listing="Stylish, Walking Distance to Centre, Free Parking",
            listing_number="Room 1",
            earnings="£240.00",
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] is not None
    assert body["confirmation_code"] == "CONF-CREATE"
    assert body["status"] == "confirmed"
    assert body["guest_name"] == "Create Test Guest"
    assert body["contact"] == "guest@example.com"
    assert body["adults"] == 2
    assert body["children"] == 1
    assert body["infants"] == 1
    assert body["start_date"] == "2026-05-10"
    assert body["end_date"] == "2026-05-12"
    assert body["nights"] == 2
    assert body["booked_date"] == "2026-04-01"
    assert body["listing"] == "Stylish, Walking Distance to Centre, Free Parking"
    assert body["listing_number"] == "Room 1"
    assert body["earnings"] == "£240.00"
    assert body["property_id"] is None

    db_booking = session.query(models.Booking).filter_by(confirmation_code="CONF-CREATE").one()
    assert db_booking.guest_name == "Create Test Guest"
    assert db_booking.adults == 2
    assert db_booking.earnings == "£240.00"


def test_create_booking_applies_schema_defaults_for_missing_optional_counts(client):
    response = client.post("/bookings/", json=_booking_payload("CONF-DEFAULTS"))

    assert response.status_code == 200
    body = response.json()
    assert body["contact"] is None
    assert body["adults"] == 0
    assert body["children"] == 0
    assert body["infants"] == 0
    assert body["booked_date"] is None
    assert body["listing"] is None
    assert body["listing_number"] is None
    assert body["earnings"] is None


def test_create_booking_rejects_payload_missing_required_fields(client, session):
    response = client.post(
        "/bookings/",
        json={
            "confirmation_code": "CONF-INVALID",
            "status": "confirmed",
            "guest_name": "Invalid Guest",
            "start_date": "2026-05-10",
        },
    )

    assert response.status_code == 422
    assert session.query(models.Booking).filter_by(confirmation_code="CONF-INVALID").first() is None


def test_list_bookings_returns_all_created_bookings(client):
    _create_booking(client, "CONF-LIST-1", guest_name="List Guest One")
    _create_booking(client, "CONF-LIST-2", guest_name="List Guest Two", end_date="2026-05-13", nights=3)

    response = client.get("/bookings/")

    assert response.status_code == 200
    bookings_by_code = {booking["confirmation_code"]: booking for booking in response.json()}
    assert set(bookings_by_code) == {"CONF-LIST-1", "CONF-LIST-2"}
    assert bookings_by_code["CONF-LIST-1"]["guest_name"] == "List Guest One"
    assert bookings_by_code["CONF-LIST-2"]["end_date"] == "2026-05-13"


def test_get_booking_returns_booking_by_confirmation_code(client):
    created = _create_booking(client, "CONF-GET", guest_name="Get Test Guest")

    response = client.get("/bookings/CONF-GET")

    assert response.status_code == 200
    assert response.json() == created


def test_get_booking_returns_404_for_unknown_confirmation_code(client):
    response = client.get("/bookings/DOES-NOT-EXIST")

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking not found"}


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


def test_delete_booking_only_removes_links_for_target_booking(client, session):
    _create_booking(client, "CONF-KEEP", guest_name="Keep Test Guest")
    _create_booking(client, "CONF-REMOVE", guest_name="Remove Test Guest")
    cleaner_response = client.post("/cleaners/", json={"name": "Selective Delete Cleaner"})
    assert cleaner_response.status_code == 200

    session_response = client.post(
        "/cleaning-sessions/",
        json={
            "cleaner_id": cleaner_response.json()["id"],
            "clean_date": "2026-05-12",
            "hours": 2,
            "minutes": 0,
            "confirmation_codes": ["CONF-KEEP", "CONF-REMOVE"],
        },
    )
    assert session_response.status_code == 200
    assert session.query(models.SessionBooking).count() == 2

    response = client.delete("/bookings/CONF-REMOVE")

    assert response.status_code == 200
    assert response.json() == {
        "deleted": "CONF-REMOVE",
        "deleted_session_bookings": 1,
    }
    assert session.query(models.Booking).filter_by(confirmation_code="CONF-REMOVE").first() is None
    assert session.query(models.Booking).filter_by(confirmation_code="CONF-KEEP").one().guest_name == "Keep Test Guest"
    remaining_links = session.query(models.SessionBooking).all()
    assert len(remaining_links) == 1
    assert remaining_links[0].confirmation_code == "CONF-KEEP"


def test_delete_booking_without_session_links_reports_zero_deleted_links(client, session):
    _create_booking(client, "CONF-NO-LINKS")

    response = client.delete("/bookings/CONF-NO-LINKS")

    assert response.status_code == 200
    assert response.json() == {
        "deleted": "CONF-NO-LINKS",
        "deleted_session_bookings": 0,
    }
    assert session.query(models.Booking).filter_by(confirmation_code="CONF-NO-LINKS").first() is None


def test_delete_booking_returns_404_for_unknown_confirmation_code(client):
    response = client.delete("/bookings/DOES-NOT-EXIST")

    assert response.status_code == 404
    assert response.json() == {"detail": "Booking not found"}
