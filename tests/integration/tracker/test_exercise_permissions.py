import json

import pytest
from django.urls import reverse

from tests.factories.tracker_factories import ExerciseFactory
from tests.factories.tracker_factories import ExerciseSetFactory
from tests.factories.tracker_factories import WorkoutPlanFactory
from tracker.models import Exercise
from tracker.models import ExerciseSet
from tracker.models import WorkoutSession

PAYLOAD = {"name": "Changed", "type": "cardio", "description": "Changed"}


def html_url(name, exercise_id):
    return reverse(f"tracker:{name}", kwargs={"exercise_id": exercise_id})


def api_url(exercise_id):
    return reverse("tracker:api_exercise_detail", kwargs={"exercise_id": exercise_id})


@pytest.mark.django_db
class TestOwnership:
    def test_html_create_assigns_owner_to_regular_user(self, auth_client, user):
        auth_client.post("/exercises/create/", {"name": "Mine", "type": "strength", "description": "Desc"})
        assert Exercise.objects.get(name="Mine").owner == user

    def test_html_create_by_staff_makes_system_exercise(self, staff_client):
        staff_client.post("/exercises/create/", {"name": "Global", "type": "strength", "description": "Desc"})
        assert Exercise.objects.get(name="Global").owner is None

    def test_api_create_assigns_owner_to_regular_user(self, auth_client, user):
        response = auth_client.post("/api/exercises/", data=json.dumps(PAYLOAD), content_type="application/json")
        assert response.status_code == 201
        assert Exercise.objects.get(id=response.json()["id"]).owner == user

    def test_api_create_by_staff_makes_system_exercise(self, staff_client):
        response = staff_client.post("/api/exercises/", data=json.dumps(PAYLOAD), content_type="application/json")
        assert Exercise.objects.get(id=response.json()["id"]).owner is None


@pytest.mark.django_db
class TestVisibility:
    def test_list_shows_system_and_own_but_not_others(self, auth_client, exercise, owned_exercise, other_exercise):
        shown = {e.id for e in auth_client.get("/exercises/").context["exercises"]}
        assert shown == {exercise.id, owned_exercise.id}

    def test_list_for_anonymous_shows_only_system(self, client, exercise, owned_exercise):
        shown = {e.id for e in client.get("/exercises/").context["exercises"]}
        assert shown == {exercise.id}

    def test_detail_of_others_private_exercise_is_404(self, auth_client, other_exercise):
        assert auth_client.get(html_url("exercise_detail", other_exercise.id)).status_code == 404

    def test_detail_of_own_exercise_is_200(self, auth_client, owned_exercise):
        assert auth_client.get(html_url("exercise_detail", owned_exercise.id)).status_code == 200

    def test_api_list_hides_others_private_exercises(self, auth_client, exercise, owned_exercise, other_exercise):
        ids = {e["id"] for e in auth_client.get("/api/exercises/").json()["results"]}
        assert ids == {exercise.id, owned_exercise.id}

    def test_api_detail_of_others_private_exercise_is_404(self, auth_client, other_exercise):
        assert auth_client.get(api_url(other_exercise.id)).status_code == 404

    def test_add_exercise_form_offers_only_visible_exercises(self, auth_client, plan, exercise, other_exercise):
        url = reverse("tracker:plan_add_exercise", kwargs={"plan_id": plan.id})
        shown = {e.id for e in auth_client.get(url).context["exercises"]}
        assert shown == {exercise.id}


@pytest.mark.django_db
class TestHtmlCatalogPermissions:
    @pytest.mark.parametrize("view", ["exercise_update", "exercise_delete"])
    def test_regular_user_cannot_touch_system_exercise(self, auth_client, exercise, view):
        response = auth_client.post(html_url(view, exercise.id), PAYLOAD)
        assert response.status_code == 403
        exercise.refresh_from_db()
        assert exercise.name != "Changed"

    @pytest.mark.parametrize("view", ["exercise_update", "exercise_delete"])
    def test_regular_user_cannot_touch_others_private_exercise(self, auth_client, other_exercise, view):
        assert auth_client.post(html_url(view, other_exercise.id), PAYLOAD).status_code == 404
        assert Exercise.objects.filter(id=other_exercise.id).exists()

    def test_update_form_of_system_exercise_is_forbidden_for_regular_user(self, auth_client, exercise):
        assert auth_client.get(html_url("exercise_update", exercise.id)).status_code == 403

    def test_owner_can_update_own_exercise(self, auth_client, owned_exercise):
        auth_client.post(html_url("exercise_update", owned_exercise.id), PAYLOAD)
        owned_exercise.refresh_from_db()
        assert owned_exercise.name == "Changed"

    def test_owner_can_delete_own_exercise(self, auth_client, owned_exercise):
        auth_client.post(html_url("exercise_delete", owned_exercise.id))
        assert not Exercise.objects.filter(id=owned_exercise.id).exists()

    def test_staff_can_update_system_exercise(self, staff_client, exercise):
        staff_client.post(html_url("exercise_update", exercise.id), PAYLOAD)
        exercise.refresh_from_db()
        assert exercise.name == "Changed"

    def test_staff_can_delete_system_exercise(self, staff_client, exercise):
        staff_client.post(html_url("exercise_delete", exercise.id))
        assert not Exercise.objects.filter(id=exercise.id).exists()

    def test_staff_cannot_touch_others_private_exercise(self, staff_client, other_exercise):
        assert staff_client.post(html_url("exercise_delete", other_exercise.id)).status_code == 404
        assert Exercise.objects.filter(id=other_exercise.id).exists()


@pytest.mark.django_db
class TestApiCatalogPermissions:
    def send(self, client, method, exercise_id):
        return getattr(client, method)(
            api_url(exercise_id),
            data=json.dumps(PAYLOAD),
            content_type="application/json",
        )

    @pytest.mark.parametrize("method", ["put", "patch", "delete"])
    def test_regular_user_cannot_modify_system_exercise(self, auth_client, exercise, method):
        assert self.send(auth_client, method, exercise.id).status_code == 403
        exercise.refresh_from_db()
        assert exercise.name != "Changed"

    @pytest.mark.parametrize("method", ["put", "patch", "delete"])
    def test_regular_user_cannot_modify_others_private_exercise(self, auth_client, other_exercise, method):
        assert self.send(auth_client, method, other_exercise.id).status_code == 404
        assert Exercise.objects.filter(id=other_exercise.id).exists()

    @pytest.mark.parametrize("method", ["put", "patch"])
    def test_owner_can_update_own_exercise(self, auth_client, owned_exercise, method):
        assert self.send(auth_client, method, owned_exercise.id).status_code == 200
        owned_exercise.refresh_from_db()
        assert owned_exercise.name == "Changed"

    def test_owner_can_delete_own_exercise(self, auth_client, owned_exercise):
        assert self.send(auth_client, "delete", owned_exercise.id).status_code == 204
        assert not Exercise.objects.filter(id=owned_exercise.id).exists()

    @pytest.mark.parametrize(("method", "expected"), [("put", 200), ("patch", 200), ("delete", 204)])
    def test_staff_can_modify_system_exercise(self, staff_client, exercise, method, expected):
        assert self.send(staff_client, method, exercise.id).status_code == expected
        if method == "delete":
            assert not Exercise.objects.filter(id=exercise.id).exists()
        else:
            exercise.refresh_from_db()
            assert exercise.name == "Changed"

    def test_create_ignores_owner_in_payload(self, auth_client, user, other_user):
        payload = {**PAYLOAD, "owner": other_user.id, "owner_id": other_user.id}
        response = auth_client.post("/api/exercises/", data=json.dumps(payload), content_type="application/json")
        assert Exercise.objects.get(id=response.json()["id"]).owner == user

    def test_update_ignores_owner_in_payload(self, auth_client, owned_exercise, user, other_user):
        payload = {**PAYLOAD, "owner": other_user.id}
        auth_client.patch(api_url(owned_exercise.id), data=json.dumps(payload), content_type="application/json")
        owned_exercise.refresh_from_db()
        assert owned_exercise.owner == user


@pytest.mark.django_db
class TestPlanOwnershipHoles:
    def test_cannot_add_others_private_exercise_to_own_plan(self, auth_client, plan, other_exercise):
        url = reverse("tracker:plan_add_exercise", kwargs={"plan_id": plan.id})
        auth_client.post(url, {"exercise_id": other_exercise.id, "sets": 3, "reps": 10, "weight": 0})
        assert not ExerciseSet.objects.filter(workout_plan=plan, exercise=other_exercise).exists()

    def test_can_add_own_private_exercise_to_own_plan(self, auth_client, plan, owned_exercise):
        url = reverse("tracker:plan_add_exercise", kwargs={"plan_id": plan.id})
        auth_client.post(url, {"exercise_id": owned_exercise.id, "sets": 3, "reps": 10, "weight": 0})
        assert ExerciseSet.objects.filter(workout_plan=plan, exercise=owned_exercise).exists()

    def test_cannot_delete_exercise_set_from_others_plan(self, auth_client, other_user):
        foreign_plan = WorkoutPlanFactory(creator=other_user)
        es = ExerciseSetFactory(workout_plan=foreign_plan, exercise=ExerciseFactory())
        auth_client.post(reverse("tracker:exercise_set_delete", kwargs={"es_id": es.id}))
        assert ExerciseSet.objects.filter(id=es.id).exists()

    def test_cannot_start_session_on_others_plan(self, auth_client, user, other_user):
        foreign_plan = WorkoutPlanFactory(creator=other_user)
        auth_client.post(reverse("tracker:session_start", kwargs={"plan_id": foreign_plan.id}))
        assert not WorkoutSession.objects.filter(user=user, plan=foreign_plan).exists()


@pytest.mark.django_db
class TestDeletingUsedExercise:
    @pytest.fixture
    def used_exercise(self, exercise, plan):
        ExerciseSetFactory(workout_plan=plan, exercise=exercise)
        return exercise

    def test_html_delete_is_refused_and_keeps_plans_intact(self, staff_client, used_exercise, plan):
        response = staff_client.post(html_url("exercise_delete", used_exercise.id), follow=True)
        assert Exercise.objects.filter(id=used_exercise.id).exists()
        assert ExerciseSet.objects.filter(workout_plan=plan).count() == 1
        assert b"used in 1 plan" in response.content

    def test_api_delete_answers_409_and_keeps_plans_intact(self, staff_client, used_exercise, plan):
        response = staff_client.delete(api_url(used_exercise.id))
        assert response.status_code == 409
        assert ExerciseSet.objects.filter(workout_plan=plan).count() == 1

    def test_unused_exercise_can_still_be_deleted(self, staff_client, exercise):
        assert staff_client.delete(api_url(exercise.id)).status_code == 204
