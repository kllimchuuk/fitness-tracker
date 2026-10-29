import pytest

from tests.factories.user_factory import UserFactory

LOGIN_URL = "/authentication/login/"


@pytest.mark.django_db
class TestLoginView:
    def test_get_returns_200(self, client):
        response = client.get(LOGIN_URL)
        assert response.status_code == 200

    def test_valid_credentials_redirect_to_home(self, client, db):
        UserFactory(email="user@test.com", password="testpass123")
        response = client.post(LOGIN_URL, {"email": "user@test.com", "password": "testpass123"})
        assert response.status_code == 302
        assert response["Location"] == "/"

    def test_valid_credentials_sets_session(self, client, db):
        user = UserFactory(email="user@test.com", password="testpass123")
        client.post(LOGIN_URL, {"email": "user@test.com", "password": "testpass123"})
        assert client.session.get("user_id") == user.id
        assert client.session.get("email") == "user@test.com"

    def test_wrong_password_returns_error(self, client, db):
        UserFactory(email="user@test.com", password="testpass123")
        response = client.post(LOGIN_URL, {"email": "user@test.com", "password": "wrongpassword"})
        assert response.status_code == 200
        assert b"Invalid credentials" in response.content

    def test_nonexistent_email_returns_error(self, client):
        response = client.post(LOGIN_URL, {"email": "nobody@test.com", "password": "testpass123"})
        assert response.status_code == 200
        assert b"Invalid credentials" in response.content

    def test_empty_email_returns_error(self, client):
        response = client.post(LOGIN_URL, {"email": "", "password": "testpass123"})
        assert response.status_code == 200
        assert b"Invalid credentials" in response.content

    def test_empty_password_returns_error(self, client):
        response = client.post(LOGIN_URL, {"email": "user@test.com", "password": ""})
        assert response.status_code == 200
        assert b"Invalid credentials" in response.content

    def test_invalid_email_format_returns_error(self, client):
        response = client.post(LOGIN_URL, {"email": "notanemail", "password": "testpass123"})
        assert response.status_code == 200
        assert b"Invalid credentials" in response.content

    def test_wrong_password_does_not_set_session(self, client, db):
        UserFactory(email="user@test.com", password="testpass123")
        client.post(LOGIN_URL, {"email": "user@test.com", "password": "wrongpassword"})
        assert client.session.get("user_id") is None
