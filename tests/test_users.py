from app import models
from app.security import verify_password
from .database import client, session


def create_user(client, email="user@example.com", password="secure-pass", **fields):
    return client.post(
        "/users/", json={"email": email, "password": password, **fields}
    )


def test_create_and_get_user_without_exposing_password(client, session):
    response = create_user(client)

    assert response.status_code == 201
    assert response.json() == {
        "id": response.json()["id"],
        "email": "user@example.com",
        "role": "user",
    }
    user = session.get(models.User, response.json()["id"])
    assert user.hashed_password != "secure-pass"
    assert verify_password("secure-pass", user.hashed_password)

    fetched = client.get(f"/users/{user.id}")
    assert fetched.status_code == 200
    assert fetched.json() == response.json()


def test_list_users(client):
    create_user(client, "first@example.com")
    create_user(client, "second@example.com")

    response = client.get("/users/")

    assert response.status_code == 200
    assert [user["email"] for user in response.json()] == [
        "first@example.com",
        "second@example.com",
    ]
    assert all(
        "password" not in user and "hashed_password" not in user
        for user in response.json()
    )


def test_update_user_email_and_password(client, session):
    user_id = create_user(client).json()["id"]

    response = client.patch(
        f"/users/{user_id}",
        json={
            "email": "updated@example.com",
            "password": "new-password",
            "role": "admin",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": user_id,
        "email": "updated@example.com",
        "role": "admin",
    }
    session.expire_all()
    user = session.get(models.User, user_id)
    assert verify_password("new-password", user.hashed_password)
    assert not verify_password("secure-pass", user.hashed_password)
    assert user.role == "admin"


def test_create_user_with_role(client, session):
    response = create_user(client, role="manager")

    assert response.status_code == 201
    assert response.json()["role"] == "manager"
    assert session.get(models.User, response.json()["id"]).role == "manager"


def test_delete_user(client):
    user_id = create_user(client).json()["id"]

    assert client.delete(f"/users/{user_id}").status_code == 204
    assert client.get(f"/users/{user_id}").status_code == 404
    assert client.delete(f"/users/{user_id}").status_code == 404


def test_duplicate_email_returns_conflict(client):
    assert create_user(client).status_code == 201
    response = create_user(client)
    assert response.status_code == 409
    assert response.json() == {"detail": "Email already registered"}


def test_user_validation_and_not_found_responses(client):
    assert (
        create_user(client, email="invalid", password="secure-pass").status_code == 422
    )
    assert create_user(client, password="short").status_code == 422
    assert client.get("/users/999").status_code == 404
    assert (
        client.patch("/users/999", json={"email": "new@example.com"}).status_code
        == 404
    )
