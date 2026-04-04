import pytest
from django.contrib.auth.hashers import check_password

PROFILE_URL = "/authentication/profile/"
PROFILE_EDIT_URL = "/authentication/profile/edit/"
PROFILE_PASSWORD_URL = "/authentication/profile/password/"
LOGIN_URL = "/authentication/login/"


@pytest.mark.django_db
class TestProfileView:
    def test_profile_requires_auth(self, client):
        response = client.get(PROFILE_URL)
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]

    def test_profile_returns_200_when_authenticated(self, auth_client):
        response = auth_client.get(PROFILE_URL)
        assert response.status_code == 200

    def test_profile_shows_user_data(self, auth_client, user):
        response = auth_client.get(PROFILE_URL)
        content = response.content.decode()
        assert user.email in content


@pytest.mark.django_db
class TestProfileEditView:
    def test_edit_requires_auth(self, client):
        response = client.get(PROFILE_EDIT_URL)
        assert response.status_code == 302

    def test_get_returns_200_when_authenticated(self, auth_client):
        response = auth_client.get(PROFILE_EDIT_URL)
        assert response.status_code == 200

    def test_edit_updates_age(self, auth_client, user):
        auth_client.post(PROFILE_EDIT_URL, {"age": "30", "height": "", "goal": ""})
        user.refresh_from_db()
        assert user.age == 30

    def test_edit_updates_height(self, auth_client, user):
        auth_client.post(PROFILE_EDIT_URL, {"age": "", "height": "180", "goal": ""})
        user.refresh_from_db()
        assert user.height == 180.0

    def test_edit_updates_goal(self, auth_client, user):
        auth_client.post(PROFILE_EDIT_URL, {"age": "", "height": "", "goal": "Lose weight"})
        user.refresh_from_db()
        assert user.goal == "Lose weight"

    def test_edit_redirects_to_profile_on_success(self, auth_client):
        response = auth_client.post(PROFILE_EDIT_URL, {"age": "28", "height": "", "goal": ""})
        assert response.status_code == 302
        assert PROFILE_URL in response["Location"]

    def test_edit_with_invalid_age_returns_error(self, auth_client):
        response = auth_client.post(PROFILE_EDIT_URL, {"age": "200", "height": "", "goal": ""})
        assert response.status_code == 200
        assert b"Invalid age" in response.content

    def test_edit_with_invalid_height_returns_error(self, auth_client):
        response = auth_client.post(PROFILE_EDIT_URL, {"age": "", "height": "5", "goal": ""})
        assert response.status_code == 200
        assert b"Invalid height" in response.content


@pytest.mark.django_db
class TestChangePasswordView:
    def test_change_password_requires_auth(self, client):
        response = client.get(PROFILE_PASSWORD_URL)
        assert response.status_code == 302

    def test_get_returns_200_when_authenticated(self, auth_client):
        response = auth_client.get(PROFILE_PASSWORD_URL)
        assert response.status_code == 200

    def test_valid_password_change_redirects_to_profile(self, auth_client):
        response = auth_client.post(
            PROFILE_PASSWORD_URL,
            {
                "current_password": "testpass123",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 302
        assert PROFILE_URL in response["Location"]

    def test_valid_password_change_updates_password(self, auth_client, user):
        auth_client.post(
            PROFILE_PASSWORD_URL,
            {
                "current_password": "testpass123",
                "new_password": "newpassword456",
            },
        )
        user.refresh_from_db()
        assert check_password("newpassword456", user.password)

    def test_wrong_current_password_returns_error(self, auth_client):
        response = auth_client.post(
            PROFILE_PASSWORD_URL,
            {
                "current_password": "wrongpassword",
                "new_password": "newpassword456",
            },
        )
        assert response.status_code == 200
        assert b"Incorrect current password" in response.content

    def test_same_password_returns_error(self, auth_client):
        response = auth_client.post(
            PROFILE_PASSWORD_URL,
            {
                "current_password": "testpass123",
                "new_password": "testpass123",
            },
        )
        assert response.status_code == 200
        assert b"matches the old one" in response.content

    def test_new_password_too_short_returns_error(self, auth_client):
        response = auth_client.post(
            PROFILE_PASSWORD_URL,
            {
                "current_password": "testpass123",
                "new_password": "short",
            },
        )
        assert response.status_code == 200
        assert b"least 8 characters" in response.content
