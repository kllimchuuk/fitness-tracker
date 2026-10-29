import json

import pytest
from django.urls import reverse

from tests.factories.tracker_factories import ExerciseFactory
from tracker.models import Exercise


@pytest.mark.django_db
class TestApiExerciseList:
    url = "/api/exercises/"

    def test_get_returns_all_exercises(self, auth_client):
        ExerciseFactory.create_batch(3)
        response = auth_client.get(self.url)
        assert response.status_code == 200
        assert len(response.json()["results"]) == 3

    def test_get_returns_empty_list_when_no_exercises(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == 200
        assert response.json()["results"] == []

    def test_get_requires_auth(self, client):
        response = client.get(self.url)
        assert response.status_code == 401

    def test_get_filters_by_search(self, auth_client):
        ExerciseFactory(name="Squat")
        ExerciseFactory(name="Bench Press")
        response = auth_client.get(self.url + "?search=squat")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["name"] == "Squat"

    def test_get_filters_by_type(self, auth_client):
        ExerciseFactory(type="strength")
        ExerciseFactory(type="cardio")
        ExerciseFactory(type="cardio")
        response = auth_client.get(self.url + "?type=cardio")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 2

    def test_post_creates_exercise(self, auth_client):
        payload = {"name": "Deadlift", "type": "strength", "description": "Hip hinge movement"}
        response = auth_client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Deadlift"
        assert data["type"] == "strength"
        assert data["description"] == "Hip hinge movement"

    def test_post_creates_exercise_without_description(self, auth_client):
        payload = {"name": "Pull-up", "type": "strength"}
        response = auth_client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["description"] == ""

    def test_post_returns_400_when_name_missing(self, auth_client):
        payload = {"type": "strength"}
        response = auth_client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_post_returns_400_when_type_missing(self, auth_client):
        payload = {"name": "Push-up"}
        response = auth_client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_post_returns_400_for_invalid_json(self, auth_client):
        response = auth_client.post(
            self.url,
            data="not valid json",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_post_requires_auth(self, client):
        payload = {"name": "Squat", "type": "strength"}
        response = client.post(
            self.url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestApiExerciseDetail:
    def url(self, exercise_id):
        return reverse("tracker:api_exercise_detail", kwargs={"exercise_id": exercise_id})

    def test_get_returns_exercise(self, auth_client, exercise):
        response = auth_client.get(self.url(exercise.id))
        assert response.status_code == 200
        assert response.json()["id"] == exercise.id
        assert response.json()["name"] == exercise.name

    def test_get_returns_404_for_nonexistent(self, auth_client):
        response = auth_client.get(self.url(99999))
        assert response.status_code == 404

    def test_get_requires_auth(self, client, exercise):
        response = client.get(self.url(exercise.id))
        assert response.status_code == 401

    def test_put_updates_all_fields(self, auth_client, exercise):
        payload = {"name": "Updated Name", "type": "cardio", "description": "Updated desc"}
        response = auth_client.put(
            self.url(exercise.id),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["type"] == "cardio"
        assert data["description"] == "Updated desc"

    def test_put_returns_400_when_name_missing(self, auth_client, exercise):
        payload = {"type": "cardio"}
        response = auth_client.put(
            self.url(exercise.id),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_patch_updates_single_field(self, auth_client, exercise):
        payload = {"name": "Patched Name"}
        response = auth_client.patch(
            self.url(exercise.id),
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Patched Name"
        assert response.json()["type"] == exercise.type

    def test_patch_returns_404_for_nonexistent(self, auth_client):
        response = auth_client.patch(
            self.url(99999),
            data=json.dumps({"name": "x"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_delete_removes_exercise(self, auth_client, exercise):
        exercise_id = exercise.id
        response = auth_client.delete(self.url(exercise_id))
        assert response.status_code == 204
        assert not Exercise.objects.filter(id=exercise_id).exists()

    def test_delete_returns_404_for_nonexistent(self, auth_client):
        response = auth_client.delete(self.url(99999))
        assert response.status_code == 404

    def test_delete_requires_auth(self, client, exercise):
        response = client.delete(self.url(exercise.id))
        assert response.status_code == 401
