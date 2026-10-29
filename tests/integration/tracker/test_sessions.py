import pytest
from django.urls import reverse

from tests.factories.tracker_factories import WorkoutSessionFactory
from tracker.models import WorkoutSession

LOGIN_URL = "/authentication/login/"


@pytest.mark.django_db
class TestWorkoutSessionListView:
    url = "/sessions/"

    def test_list_requires_auth(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]

    def test_list_returns_200(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == 200

    def test_list_shows_only_user_sessions(self, auth_client, user):
        WorkoutSessionFactory(user=user)
        WorkoutSessionFactory(user=user)
        WorkoutSessionFactory()  # other user's session
        response = auth_client.get(self.url)
        assert len(response.context["sessions"]) == 2

    def test_list_shows_empty_for_new_user(self, auth_client):
        response = auth_client.get(self.url)
        assert len(response.context["sessions"]) == 0


@pytest.mark.django_db
class TestWorkoutSessionStartView:
    def url(self, plan_id):
        return reverse("tracker:session_start", kwargs={"plan_id": plan_id})

    def test_start_requires_auth(self, client, plan):
        response = client.post(self.url(plan.id))
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]

    def test_start_creates_active_session(self, auth_client, user, plan):
        auth_client.post(self.url(plan.id))
        assert WorkoutSession.objects.filter(user=user, plan=plan, status="active").exists()

    def test_start_redirects_to_sessions_list(self, auth_client, plan):
        response = auth_client.post(self.url(plan.id))
        assert response.status_code == 302
        assert "/sessions/" in response["Location"]

    def test_start_fails_when_active_session_exists(self, auth_client, user, plan):
        WorkoutSessionFactory(user=user, status="active")
        auth_client.post(self.url(plan.id))
        # Only one active session should exist
        assert WorkoutSession.objects.filter(user=user, status="active").count() == 1

    def test_start_for_nonexistent_plan_redirects(self, auth_client):
        response = auth_client.post(self.url(99999))
        assert response.status_code == 302


@pytest.mark.django_db
class TestWorkoutSessionDetailView:
    def url(self, session_id):
        return reverse("tracker:session_detail", kwargs={"session_id": session_id})

    def test_detail_requires_auth(self, client, active_session):
        response = client.get(self.url(active_session.id))
        assert response.status_code == 302

    def test_detail_returns_200(self, auth_client, active_session):
        response = auth_client.get(self.url(active_session.id))
        assert response.status_code == 200

    def test_detail_returns_error_for_another_users_session(self, auth_client):
        other_session = WorkoutSessionFactory()
        response = auth_client.get(self.url(other_session.id))
        assert response.status_code == 302

    def test_post_complete_changes_status(self, auth_client, active_session):
        auth_client.post(self.url(active_session.id), {"status": "completed"})
        active_session.refresh_from_db()
        assert active_session.status == WorkoutSession.Status.COMPLETED

    def test_post_complete_sets_duration(self, auth_client, active_session):
        auth_client.post(self.url(active_session.id), {"status": "completed"})
        active_session.refresh_from_db()
        assert active_session.duration_minutes >= 0

    def test_post_delete_removes_session(self, auth_client, active_session):
        session_id = active_session.id
        auth_client.post(self.url(active_session.id), {"status": "delete"})
        assert not WorkoutSession.objects.filter(id=session_id).exists()

    def test_post_unknown_action_redirects(self, auth_client, active_session):
        response = auth_client.post(self.url(active_session.id), {"status": "unknown"})
        assert response.status_code == 302

    def test_post_complete_redirects_to_sessions_list(self, auth_client, active_session):
        response = auth_client.post(self.url(active_session.id), {"status": "completed"})
        assert response.status_code == 302
        assert "/sessions/" in response["Location"]

    def test_post_complete_already_completed_session_shows_error(self, auth_client, completed_session):
        response = auth_client.post(self.url(completed_session.id), {"status": "completed"})
        assert response.status_code == 302
