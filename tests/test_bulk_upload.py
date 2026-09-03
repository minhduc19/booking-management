import csv
from pathlib import Path

from app import models
from .database import client, session

def test_bulk_upload_bookings_from_payload(client, session):
    payload_path = Path(__file__).with_name("BookingTestPayload.csv")

    with payload_path.open("r", encoding="utf-8", newline="") as csv_file:
        csv_rows = list(csv.DictReader(csv_file))

    expected_rows = len(csv_rows)
    expected_listing_metadata = len({row["Listing"] for row in csv_rows})

    with payload_path.open("rb") as csv_file:
        response = client.post(
            "/bookings/bulk-upload/",
            files={"files": (payload_path.name, csv_file, "text/csv")},
        )

    assert response.status_code == 200

    body = response.json()
    assert body["files_processed"] == 1
    assert body["created"] == expected_rows
    assert body["updated"] == 0
    assert body["errors"] == []
    assert len(body["created_codes"]) == expected_rows

    total_bookings = session.query(models.Booking).count()
    total_properties = session.query(models.Property).count()
    total_listing_metadata = session.query(models.ListingMetadata).count()
    unmapped_bookings = (
        session.query(models.Booking)
        .filter(models.Booking.listing_number.is_(None))
        .count()
    )

    assert total_bookings == expected_rows
    assert total_properties == 2
    assert total_listing_metadata == expected_listing_metadata
    assert unmapped_bookings == 0


def test_bulk_upload_bookings_from_transaction_history_csv(client, session):
    payload = """Date,Type,Confirmation Code,Booking date,Start date,End date,Nights,Guest,Listing,Details,Reference code,Currency,Amount,Service fee,Cleaning fee,Community fee,Gross earnings,Airbnb remitted tax,Earnings year
09/03/2026,Reservation,HM8PNJJMTA,08/03/2026,09/02/2026,09/04/2026,2,Sekar Anggraeni,"Cosy, Walking Distance to Centre, Free Parking",,,GBP,144.82,33.08,12.00,7.90,172.39,0.00,
"""

    response = client.post(
        "/bookings/bulk-upload/",
        files={"files": ("transaction-history.csv", payload, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["created"] == 1
    assert response.json()["errors"] == []

    booking = (
        session.query(models.Booking)
        .filter_by(confirmation_code="HM8PNJJMTA")
        .one()
    )
    assert booking.status == "Reservation"
    assert booking.guest_name == "Sekar Anggraeni"
    assert booking.start_date.isoformat() == "2026-02-09"
    assert booking.end_date.isoformat() == "2026-04-09"
    assert booking.booked_date.isoformat() == "2026-03-08"
    assert booking.nights == 2
    assert booking.adults == booking.children == booking.infants == 0
    assert booking.earnings == "172.39"


def test_bulk_upload_supports_us_transaction_history_dates(client, session):
    payload = """Date,Type,Confirmation Code,Booking date,Start date,End date,Nights,Guest,Listing,Details,Reference code,Currency,Amount,Service fee,Cleaning fee,Community fee,Gross earnings,Airbnb remitted tax,Earnings year
06/29/2026,Reservation,USDATE123,06/28/2026,07/02/2026,07/04/2026,2,Jane Doe,US date listing,,,GBP,144.82,33.08,12.00,7.90,172.39,0.00,
"""

    response = client.post(
        "/bookings/bulk-upload/",
        files={"files": ("us-transaction-history.csv", payload, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["created"] == 1
    assert response.json()["errors"] == []

    booking = session.query(models.Booking).filter_by(confirmation_code="USDATE123").one()
    assert booking.start_date.isoformat() == "2026-07-02"
    assert booking.end_date.isoformat() == "2026-07-04"
    assert booking.booked_date.isoformat() == "2026-06-28"


def test_bulk_upload_deduplicates_confirmation_codes_in_uploaded_files(client, session):
    payload = """Date,Type,Confirmation Code,Booking date,Start date,End date,Nights,Guest,Listing
09/03/2026,Reservation,HMKHMEBEHS,08/03/2026,09/02/2026,09/04/2026,2,Harry Smith,Spacious - central - historic view
09/03/2026,Co-Host payout,HMKHMEBEHS,08/03/2026,09/02/2026,09/05/2026,3,Harry Smith,Spacious - central - historic view
"""

    response = client.post(
        "/bookings/bulk-upload/",
        files={"files": ("duplicate-confirmation-codes.csv", payload, "text/csv")},
    )

    assert response.status_code == 200
    assert response.json()["created"] == 1
    assert response.json()["updated"] == 0
    assert response.json()["errors"] == []
    assert session.query(models.Booking).count() == 1

    booking = (
        session.query(models.Booking)
        .filter_by(confirmation_code="HMKHMEBEHS")
        .one()
    )
    assert booking.status == "Co-Host payout"
    assert booking.nights == 3
