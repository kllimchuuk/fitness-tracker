import pytest

from authentication.models import User
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

    def test_valid_credentials_logs_user_in(self, client, db):
        user = UserFactory(email="user@test.com", password="testpass123")
        client.post(LOGIN_URL, {"email": "user@test.com", "password": "testpass123"})
        assert client.session.get("_auth_user_id") == str(user.id)

    def test_email_is_case_insensitive_on_domain(self, client, db):
        user = UserFactory(email="user@test.com", password="testpass123")
        client.post(LOGIN_URL, {"email": "user@TEST.com", "password": "testpass123"})
        assert client.session.get("_auth_user_id") == str(user.id)

    def test_inactive_user_cannot_log_in(self, client, db):
        UserFactory(email="user@test.com", password="testpass123", is_active=False)
        response = client.post(LOGIN_URL, {"email": "user@test.com", "password": "testpass123"})
        assert response.status_code == 200
        assert b"Invalid credentials" in response.content
        assert "_auth_user_id" not in client.session

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

    def test_wrong_password_does_not_log_in(self, client, db):
        UserFactory(email="user@test.com", password="testpass123")
        client.post(LOGIN_URL, {"email": "user@test.com", "password": "wrongpassword"})
        assert "_auth_user_id" not in client.session


@pytest.mark.django_db
class TestLegacyEmails:
    @pytest.fixture
    def legacy_user(self):
        # created before normalize_email was applied: the domain keeps its capitals
        return UserFactory(email="legacy@Gmail.com", password="testpass123")

    @pytest.mark.parametrize("typed", ["legacy@Gmail.com", "legacy@gmail.com", "LEGACY@gmail.com"])
    def test_legacy_user_can_log_in_whatever_the_case(self, client, legacy_user, typed):
        client.post(LOGIN_URL, {"email": typed, "password": "testpass123"})
        assert client.session.get("_auth_user_id") == str(legacy_user.id)

    def test_cannot_register_a_case_variant_of_an_existing_email(self, client, legacy_user):
        response = client.post(
            "/authentication/register/",
            {"email": "legacy@gmail.com", "password": "securepass123", "age": "25", "height": "175", "goal": "x"},
        )
        assert b"already exists" in response.content
        assert User.objects.count() == 1


@pytest.mark.django_db
class TestNextRedirect:
    def login(self, client, query):
        UserFactory(email="user@test.com", password="testpass123")
        return client.post(LOGIN_URL + query, {"email": "user@test.com", "password": "testpass123"})

    def test_safe_next_is_followed(self, client):
        assert self.login(client, "?next=/plans/")["Location"] == "/plans/"

    def test_protected_page_round_trip(self, client):
        UserFactory(email="user@test.com", password="testpass123")
        location = client.get("/plans/")["Location"]
        response = client.post(location, {"email": "user@test.com", "password": "testpass123"})
        assert response["Location"] == "/plans/"

    @pytest.mark.parametrize("evil", ["https://evil.com/", "//evil.com/", "javascript:alert(1)"])
    def test_unsafe_next_falls_back_to_home(self, client, evil):
        assert self.login(client, f"?next={evil}")["Location"] == "/"


@pytest.mark.django_db
class TestSessionInvalidation:
    def test_deactivated_users_existing_session_is_dropped(self, auth_client, user):
        user.is_active = False
        user.save()
        response = auth_client.get("/authentication/profile/")
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]


@pytest.mark.django_db
class TestLogoutView:
    url = "/authentication/logout/"

    def test_get_is_not_allowed(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == 405
        assert "_auth_user_id" in auth_client.session

    def test_post_logs_user_out_and_redirects_to_login(self, auth_client):
        response = auth_client.post(self.url)
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]
        assert "_auth_user_id" not in auth_client.session

    def test_post_when_anonymous_redirects_to_login(self, client):
        response = client.post(self.url)
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]
