from .database import client, session
from app import models


def test_listing_metadata_page(client):
    response = client.get("/index-listing-metadata")

    assert response.status_code == 200
    assert "Listing Metadata" in response.text
    assert "/listing-metadata/" in response.text


def test_listing_metadata_crud(client, session):
    property_id = session.query(models.Property).first().id
    payload = {
        "listing": "Newly added listing",
        "listing_number": "Suite 9",
        "property_id": property_id,
    }

    created = client.post("/listing-metadata/", json=payload)
    assert created.status_code == 201
    metadata_id = created.json()["id"]
    assert created.json()["property"]["id"] == property_id

    listed = client.get("/listing-metadata/")
    assert listed.status_code == 200
    assert any(item["id"] == metadata_id for item in listed.json())

    fetched = client.get(f"/listing-metadata/{metadata_id}")
    assert fetched.status_code == 200
    assert fetched.json()["listing"] == payload["listing"]

    updated = client.patch(
        f"/listing-metadata/{metadata_id}", json={"listing_number": "Suite 10"}
    )
    assert updated.status_code == 200
    assert updated.json()["listing_number"] == "Suite 10"

    deleted = client.delete(f"/listing-metadata/{metadata_id}")
    assert deleted.status_code == 204
    assert deleted.content == b""

    assert client.get(f"/listing-metadata/{metadata_id}").status_code == 404


def test_listing_metadata_rejects_unknown_property_and_duplicate_listing(client):
    invalid_property = client.post(
        "/listing-metadata/", json={"listing": "Invalid property", "property_id": 99999}
    )
    assert invalid_property.status_code == 404

    duplicate = client.post(
        "/listing-metadata/",
        json={"listing": "Spacious cosy room with prime location"},
    )
    assert duplicate.status_code == 409
