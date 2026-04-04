import pytest
from django.urls import reverse

from tests.factories.tracker_factories import ExerciseFactory
from tracker.models import Exercise

LOGIN_URL = "/authentication/login/"


@pytest.mark.django_db
class TestExerciseListView:
    url = "/exercises/"

    def test_list_returns_200_without_auth(self, client):
        response = client.get(self.url)
        assert response.status_code == 200

    def test_list_shows_all_exercises(self, client, db):
        ExerciseFactory.create_batch(3)
        response = client.get(self.url)
        assert len(response.context["exercises"]) == 3

    def test_list_filters_by_search(self, client, db):
        ExerciseFactory(name="Squat")
        ExerciseFactory(name="Bench Press")
        response = client.get(self.url + "?search=squat")
        exercises = list(response.context["exercises"])
        assert len(exercises) == 1
        assert exercises[0].name == "Squat"

    def test_list_filters_by_type(self, client, db):
        ExerciseFactory(type="strength")
        ExerciseFactory(type="cardio")
        ExerciseFactory(type="cardio")
        response = client.get(self.url + "?type=cardio")
        exercises = list(response.context["exercises"])
        assert len(exercises) == 2

    def test_list_empty_search_returns_all(self, client, db):
        ExerciseFactory.create_batch(2)
        response = client.get(self.url + "?search=")
        assert len(response.context["exercises"]) == 2


@pytest.mark.django_db
class TestExerciseDetailView:
    def url(self, exercise_id):
        return reverse("tracker:exercise_detail", kwargs={"exercise_id": exercise_id})

    def test_detail_returns_200_without_auth(self, client, exercise):
        response = client.get(self.url(exercise.id))
        assert response.status_code == 200

    def test_detail_shows_exercise_data(self, client, exercise):
        response = client.get(self.url(exercise.id))
        assert response.context["exercise"].id == exercise.id

    def test_detail_returns_404_for_nonexistent(self, client):
        response = client.get(self.url(99999))
        assert response.status_code == 404


@pytest.mark.django_db
class TestExerciseCreateView:
    url = "/exercises/create/"

    def test_create_requires_auth(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]

    def test_create_get_returns_200(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == 200

    def test_create_post_saves_exercise(self, auth_client):
        auth_client.post(self.url, {"name": "Deadlift", "type": "strength", "description": "Hip hinge"})
        assert Exercise.objects.filter(name="Deadlift").exists()

    def test_create_post_redirects_to_list(self, auth_client):
        response = auth_client.post(self.url, {"name": "Deadlift", "type": "strength", "description": "Hip hinge"})
        assert response.status_code == 302
        assert "/exercises/" in response["Location"]

    def test_create_post_with_missing_name_returns_form(self, auth_client):
        response = auth_client.post(self.url, {"name": "", "type": "strength", "description": "Hip hinge"})
        assert response.status_code == 200


@pytest.mark.django_db
class TestExerciseUpdateView:
    def url(self, exercise_id):
        return reverse("tracker:exercise_update", kwargs={"exercise_id": exercise_id})

    def test_update_requires_auth(self, client, exercise):
        response = client.get(self.url(exercise.id))
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]

    def test_update_get_returns_200(self, auth_client, exercise):
        response = auth_client.get(self.url(exercise.id))
        assert response.status_code == 200

    def test_update_post_saves_changes(self, auth_client, exercise):
        auth_client.post(
            self.url(exercise.id),
            {
                "name": "Updated Name",
                "type": "cardio",
                "description": "Updated desc",
            },
        )
        exercise.refresh_from_db()
        assert exercise.name == "Updated Name"
        assert exercise.type == "cardio"

    def test_update_post_redirects_to_detail(self, auth_client, exercise):
        response = auth_client.post(
            self.url(exercise.id),
            {
                "name": "Updated Name",
                "type": "cardio",
                "description": "Updated desc",
            },
        )
        assert response.status_code == 302
        assert f"/exercises/{exercise.id}/" in response["Location"]


@pytest.mark.django_db
class TestExerciseDeleteView:
    def url(self, exercise_id):
        return reverse("tracker:exercise_delete", kwargs={"exercise_id": exercise_id})

    def test_delete_requires_auth(self, client, exercise):
        response = client.post(self.url(exercise.id))
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]

    def test_delete_removes_exercise(self, auth_client, exercise):
        exercise_id = exercise.id
        auth_client.post(self.url(exercise.id))
        assert not Exercise.objects.filter(id=exercise_id).exists()

    def test_delete_redirects_to_list(self, auth_client, exercise):
        response = auth_client.post(self.url(exercise.id))
        assert response.status_code == 302
        assert "/exercises/" in response["Location"]
