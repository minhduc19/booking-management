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
