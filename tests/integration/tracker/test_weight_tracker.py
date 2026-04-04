import pytest
from django.urls import reverse

from tests.factories.tracker_factories import WeightTrackerFactory
from tracker.models import WeightTracker

LOGIN_URL = "/authentication/login/"


@pytest.mark.django_db
class TestWeightTrackerListView:
    url = "/weight-tracker/"

    def test_list_requires_auth(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]

    def test_list_returns_200(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == 200

    def test_list_shows_only_user_entries(self, auth_client, user):
        WeightTrackerFactory(user=user)
        WeightTrackerFactory(user=user)
        WeightTrackerFactory()  # other user's entry
        response = auth_client.get(self.url)
        assert len(response.context["weight_trackers"]) == 2

    def test_list_shows_empty_for_new_user(self, auth_client):
        response = auth_client.get(self.url)
        assert len(response.context["weight_trackers"]) == 0

    def test_post_creates_weight_entry(self, auth_client, user):
        auth_client.post(
            self.url,
            {
                "weight": "80.5",
                "date": "2025-01-01",
            },
        )
        assert WeightTracker.objects.filter(user=user, weight=80.5).exists()

    def test_post_redirects_to_list(self, auth_client):
        response = auth_client.post(
            self.url,
            {
                "weight": "80.5",
                "date": "2025-01-01",
            },
        )
        assert response.status_code == 302
        assert "/weight-tracker/" in response["Location"]

    def test_post_without_weight_shows_error(self, auth_client):
        response = auth_client.post(
            self.url,
            {
                "weight": "",
                "date": "2025-01-01",
            },
        )
        assert response.status_code == 302

    def test_post_without_date_shows_error(self, auth_client):
        response = auth_client.post(
            self.url,
            {
                "weight": "80.5",
                "date": "",
            },
        )
        assert response.status_code == 302


@pytest.mark.django_db
class TestWeightTrackerDetailView:
    def url(self, weight_tracker_id):
        return reverse("tracker:weight_tracker_detail", kwargs={"weight_tracker_id": weight_tracker_id})

    def test_detail_requires_auth(self, client, weight_entry):
        response = client.get(self.url(weight_entry.id))
        assert response.status_code == 302

    def test_detail_returns_200(self, auth_client, weight_entry):
        response = auth_client.get(self.url(weight_entry.id))
        assert response.status_code == 200

    def test_detail_shows_weight_data(self, auth_client, weight_entry):
        response = auth_client.get(self.url(weight_entry.id))
        assert response.context["weight"].id == weight_entry.id

    def test_detail_returns_error_for_another_users_entry(self, auth_client):
        other_entry = WeightTrackerFactory()
        response = auth_client.get(self.url(other_entry.id))
        assert response.status_code == 302

    def test_post_delete_removes_entry(self, auth_client, weight_entry):
        entry_id = weight_entry.id
        auth_client.post(self.url(weight_entry.id), {"_method": "delete"})
        assert not WeightTracker.objects.filter(id=entry_id).exists()

    def test_post_delete_redirects_to_list(self, auth_client, weight_entry):
        response = auth_client.post(self.url(weight_entry.id), {"_method": "delete"})
        assert response.status_code == 302
        assert "/weight-tracker/" in response["Location"]

    def test_post_delete_another_users_entry_shows_error(self, auth_client):
        other_entry = WeightTrackerFactory()
        response = auth_client.post(self.url(other_entry.id), {"_method": "delete"})
        assert response.status_code == 302

    def test_post_unknown_action_shows_error(self, auth_client, weight_entry):
        response = auth_client.post(self.url(weight_entry.id), {"_method": "unknown"})
        assert response.status_code == 302
