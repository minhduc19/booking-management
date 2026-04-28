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