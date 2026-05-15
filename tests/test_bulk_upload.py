import csv
from pathlib import Path

from app import models
from app.main import app
from .database import client, session
from app import schemas


def test_bulk_upload_bookings_from_payload(client, session):
    payload_path = Path(__file__).with_name("BookingTestPayload.csv")

    with payload_path.open("r", encoding="utf-8", newline="") as csv_file:
        expected_rows = sum(1 for _ in csv.DictReader(csv_file))

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

    assert total_bookings == expected_rows
    assert total_properties == 2
