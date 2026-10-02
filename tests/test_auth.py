import pytest

class TestSignup:
    def test_signup_success(self, client):
        response = client.post("/auth/signup", json={
            "name": "New User",
            "email": "newuser@example.com",
            "password": "newpass123"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "password_hash" not in data

    def test_signup_duplicate_email(self, client, test_user):
        response = client.post("/auth/signup", json={
            "name": "Duplicate",
            "email": "test@example.com",  
            "password": "pass123"
        })
        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_signup_short_password(self, client):
        response = client.post("/auth/signup", json={
            "name": "User",
            "email": "user@example.com",
            "password": "123"
        })
        assert response.status_code == 422

    def test_signup_invalid_email(self, client):
        response = client.post("/auth/signup", json={
            "name": "User",
            "email": "not-an-email",
            "password": "pass123"
        })
        assert response.status_code == 422

class TestLogin:
    def test_login_success(self, client, test_user):
        response = client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        response = client.post("/auth/login", data={
            "username": "test@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/auth/login", data={
            "username": "ghost@example.com",
            "password": "pass123"
        })
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        response = client.post("/auth/login", data={
            "username": "test@example.com"
        })
        assert response.status_code == 422