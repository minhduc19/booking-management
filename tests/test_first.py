from app.main import app
from .database import client, session
from app import schemas

def test_root(client):
    res = client.get("/")
    print(res.json().get('message'))
    assert res.json().get('message') == 'Changed to private repository'
    assert res.status_code == 200

def test_create_user(client):
    res = client.post(
        "/users/", json={"email": "hello123@gmail.com", "hashed_password": "password123"})

    new_user = schemas.UserCreate(**res.json())
    assert new_user.email == "hello123@gmail.com"
    assert res.status_code == 200