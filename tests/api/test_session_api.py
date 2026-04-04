import json

import pytest
from django.urls import reverse

from tests.factories.tracker_factories import WorkoutSessionFactory
from tracker.models import WorkoutSession


@pytest.mark.django_db
class TestSessionCompleteApi:
    def url(self, session_id):
        return reverse("tracker:session_detail", kwargs={"session_id": session_id})

    def test_complete_active_session(self, auth_client, active_session):
        response = auth_client.patch(
            self.url(active_session.id),
            data=json.dumps({"status": "completed"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        active_session.refresh_from_db()
        assert active_session.status == WorkoutSession.Status.COMPLETED

    def test_complete_session_returns_session_data(self, auth_client, active_session):
        response = auth_client.patch(
            self.url(active_session.id),
            data=json.dumps({"status": "completed"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == active_session.id
        assert data["status"] == "completed"

    def test_complete_session_requires_auth(self, client, active_session):
        response = client.patch(
            self.url(active_session.id),
            data=json.dumps({"status": "completed"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_complete_already_completed_session_returns_400(self, auth_client, completed_session):
        response = auth_client.patch(
            self.url(completed_session.id),
            data=json.dumps({"status": "completed"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_complete_returns_400_without_status_field(self, auth_client, active_session):
        response = auth_client.patch(
            self.url(active_session.id),
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_complete_returns_400_for_unknown_status(self, auth_client, active_session):
        response = auth_client.patch(
            self.url(active_session.id),
            data=json.dumps({"status": "paused"}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_complete_returns_400_for_invalid_json(self, auth_client, active_session):
        response = auth_client.patch(
            self.url(active_session.id),
            data="invalid json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_cannot_complete_another_users_session(self, auth_client):
        other_session = WorkoutSessionFactory(status="active")
        response = auth_client.patch(
            self.url(other_session.id),
            data=json.dumps({"status": "completed"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_complete_returns_404_for_nonexistent_session(self, auth_client):
        response = auth_client.patch(
            self.url(99999),
            data=json.dumps({"status": "completed"}),
            content_type="application/json",
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestSessionDeleteApi:
    """DELETE /sessions/<id>/delete/ — видалення сесії через API"""

    def url(self, session_id):
        return reverse("tracker:session_delete", kwargs={"session_id": session_id})

    def test_delete_removes_session(self, auth_client, active_session):
        session_id = active_session.id
        response = auth_client.delete(self.url(session_id))
        assert response.status_code == 204
        assert not WorkoutSession.objects.filter(id=session_id).exists()

    def test_delete_requires_auth(self, client, active_session):
        response = client.delete(self.url(active_session.id))
        assert response.status_code == 401

    def test_cannot_delete_another_users_session(self, auth_client):
        other_session = WorkoutSessionFactory()
        response = auth_client.delete(self.url(other_session.id))
        assert response.status_code == 404

    def test_delete_returns_404_for_nonexistent_session(self, auth_client):
        response = auth_client.delete(self.url(99999))
        assert response.status_code == 404
