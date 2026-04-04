import pytest

from authentication.models import User
from tests.factories.user_factory import UserFactory

REGISTER_URL = "/authentication/register/"


@pytest.mark.django_db
class TestRegisterView:
    def test_get_returns_200(self, client):
        response = client.get(REGISTER_URL)
        assert response.status_code == 200

    def test_valid_data_creates_user(self, client):
        response = client.post(
            REGISTER_URL,
            {
                "email": "newuser@test.com",
                "password": "securepass123",
                "age": "25",
                "height": "175",
                "goal": "Build muscle",
            },
        )
        assert response.status_code == 302
        assert User.objects.filter(email="newuser@test.com").exists()

    def test_valid_data_redirects_to_home(self, client):
        response = client.post(
            REGISTER_URL,
            {
                "email": "newuser@test.com",
                "password": "securepass123",
                "age": "25",
                "height": "175",
                "goal": "Build muscle",
            },
        )
        assert response["Location"] == "/"

    def test_valid_data_sets_session(self, client):
        client.post(
            REGISTER_URL,
            {
                "email": "newuser@test.com",
                "password": "securepass123",
                "age": "25",
                "height": "175",
                "goal": "Build muscle",
            },
        )
        assert "user_id" in client.session
        assert client.session["email"] == "newuser@test.com"

    def test_duplicate_email_returns_error(self, client, db):
        UserFactory(email="existing@test.com")
        response = client.post(
            REGISTER_URL,
            {
                "email": "existing@test.com",
                "password": "securepass123",
                "age": "25",
                "height": "175",
                "goal": "Build muscle",
            },
        )
        assert response.status_code == 200
        assert b"already exists" in response.content

    def test_invalid_email_format_returns_error(self, client):
        response = client.post(
            REGISTER_URL,
            {
                "email": "notanemail",
                "password": "securepass123",
                "age": "25",
                "height": "175",
                "goal": "Build muscle",
            },
        )
        assert response.status_code == 200
        assert b"Invalid email" in response.content

    def test_password_too_short_returns_error(self, client):
        response = client.post(
            REGISTER_URL,
            {
                "email": "newuser@test.com",
                "password": "short",
                "age": "25",
                "height": "175",
                "goal": "Build muscle",
            },
        )
        assert response.status_code == 200
        assert b"least 8 characters" in response.content

    def test_age_below_minimum_returns_error(self, client):
        response = client.post(
            REGISTER_URL,
            {
                "email": "newuser@test.com",
                "password": "securepass123",
                "age": "0",
                "height": "175",
                "goal": "Build muscle",
            },
        )
        assert response.status_code == 200
        assert b"Invalid age" in response.content

    def test_age_above_maximum_returns_error(self, client):
        response = client.post(
            REGISTER_URL,
            {
                "email": "newuser@test.com",
                "password": "securepass123",
                "age": "200",
                "height": "175",
                "goal": "Build muscle",
            },
        )
        assert response.status_code == 200
        assert b"Invalid age" in response.content

    def test_height_below_minimum_returns_error(self, client):
        response = client.post(
            REGISTER_URL,
            {
                "email": "newuser@test.com",
                "password": "securepass123",
                "age": "25",
                "height": "10",
                "goal": "Build muscle",
            },
        )
        assert response.status_code == 200
        assert b"Invalid height" in response.content

    def test_height_above_maximum_returns_error(self, client):
        response = client.post(
            REGISTER_URL,
            {
                "email": "newuser@test.com",
                "password": "securepass123",
                "age": "25",
                "height": "400",
                "goal": "Build muscle",
            },
        )
        assert response.status_code == 200
        assert b"Invalid height" in response.content

    def test_missing_goal_returns_error(self, client):
        response = client.post(
            REGISTER_URL,
            {
                "email": "newuser@test.com",
                "password": "securepass123",
                "age": "25",
                "height": "175",
                "goal": "",
            },
        )
        assert response.status_code == 200
        assert b"Goal is required" in response.content

    def test_non_numeric_age_returns_error(self, client):
        response = client.post(
            REGISTER_URL,
            {
                "email": "newuser@test.com",
                "password": "securepass123",
                "age": "abc",
                "height": "175",
                "goal": "Build muscle",
            },
        )
        assert response.status_code == 200
        assert b"Invalid age" in response.content
