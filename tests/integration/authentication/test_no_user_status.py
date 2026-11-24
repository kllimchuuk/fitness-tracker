import pytest

from authentication.models import User


@pytest.mark.django_db
class TestUserStatusRemoved:
    def test_model_has_no_status_field(self):
        assert "status" not in {field.name for field in User._meta.get_fields()}
        assert not hasattr(User, "Status")

    def test_profile_page_renders_without_status(self, auth_client):
        response = auth_client.get("/authentication/profile/")
        assert response.status_code == 200
        assert "status" not in response.context
