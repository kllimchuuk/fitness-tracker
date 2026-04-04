import pytest
from django.urls import reverse

from tests.factories.tracker_factories import ExerciseSetFactory
from tests.factories.tracker_factories import WorkoutPlanFactory
from tracker.models import ExerciseSet
from tracker.models import WorkoutPlan

LOGIN_URL = "/authentication/login/"


@pytest.mark.django_db
class TestWorkoutPlanListView:
    url = "/plans/"

    def test_list_requires_auth(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]

    def test_list_returns_200(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == 200

    def test_list_shows_only_user_plans(self, auth_client, user):
        WorkoutPlanFactory(creator=user)
        WorkoutPlanFactory(creator=user)
        WorkoutPlanFactory()  # other user's plan
        response = auth_client.get(self.url)
        assert len(response.context["plans"]) == 2

    def test_list_shows_empty_for_new_user(self, auth_client):
        response = auth_client.get(self.url)
        assert len(response.context["plans"]) == 0


@pytest.mark.django_db
class TestWorkoutPlanCreateView:
    url = "/plans/create/"

    def test_create_requires_auth(self, client):
        response = client.get(self.url)
        assert response.status_code == 302
        assert LOGIN_URL in response["Location"]

    def test_create_get_returns_200(self, auth_client):
        response = auth_client.get(self.url)
        assert response.status_code == 200

    def test_create_post_saves_plan(self, auth_client, user):
        auth_client.post(self.url, {"name": "My Plan", "description": "A great plan"})
        assert WorkoutPlan.objects.filter(name="My Plan", creator=user).exists()

    def test_create_post_redirects_to_list(self, auth_client):
        response = auth_client.post(self.url, {"name": "My Plan", "description": "A great plan"})
        assert response.status_code == 302
        assert "/plans/" in response["Location"]

    def test_create_post_assigns_current_user_as_creator(self, auth_client, user):
        auth_client.post(self.url, {"name": "My Plan", "description": "A great plan"})
        plan = WorkoutPlan.objects.get(name="My Plan")
        assert plan.creator == user


@pytest.mark.django_db
class TestWorkoutPlanDetailView:
    def url(self, plan_id):
        return reverse("tracker:plan_detail", kwargs={"plan_id": plan_id})

    def test_detail_requires_auth(self, client, plan):
        response = client.get(self.url(plan.id))
        assert response.status_code == 302

    def test_detail_returns_200_for_creator(self, auth_client, plan):
        response = auth_client.get(self.url(plan.id))
        assert response.status_code == 200

    def test_detail_returns_404_for_another_users_plan(self, auth_client):
        other_plan = WorkoutPlanFactory()
        response = auth_client.get(self.url(other_plan.id))
        assert response.status_code == 404

    def test_detail_shows_exercise_sets(self, auth_client, plan):
        ExerciseSetFactory.create_batch(2, workout_plan=plan)
        response = auth_client.get(self.url(plan.id))
        assert len(response.context["sets"]) == 2


@pytest.mark.django_db
class TestWorkoutPlanUpdateView:
    def url(self, plan_id):
        return reverse("tracker:plan_update", kwargs={"plan_id": plan_id})

    def test_update_requires_auth(self, client, plan):
        response = client.get(self.url(plan.id))
        assert response.status_code == 302

    def test_update_get_returns_200(self, auth_client, plan):
        response = auth_client.get(self.url(plan.id))
        assert response.status_code == 200

    def test_update_post_saves_changes(self, auth_client, plan):
        auth_client.post(self.url(plan.id), {"name": "Updated Plan", "description": "Updated desc"})
        plan.refresh_from_db()
        assert plan.name == "Updated Plan"

    def test_update_returns_404_for_another_users_plan(self, auth_client):
        other_plan = WorkoutPlanFactory()
        response = auth_client.post(self.url(other_plan.id), {"name": "Hacked", "description": "x"})
        assert response.status_code == 404


@pytest.mark.django_db
class TestWorkoutPlanDeleteView:
    def url(self, plan_id):
        return reverse("tracker:plan_delete", kwargs={"plan_id": plan_id})

    def test_delete_requires_auth(self, client, plan):
        response = client.post(self.url(plan.id))
        assert response.status_code == 302

    def test_delete_removes_plan(self, auth_client, plan):
        plan_id = plan.id
        auth_client.post(self.url(plan.id))
        assert not WorkoutPlan.objects.filter(id=plan_id).exists()

    def test_delete_redirects_to_list(self, auth_client, plan):
        response = auth_client.post(self.url(plan.id))
        assert response.status_code == 302
        assert "/plans/" in response["Location"]

    def test_delete_returns_404_for_another_users_plan(self, auth_client):
        other_plan = WorkoutPlanFactory()
        response = auth_client.post(self.url(other_plan.id))
        assert response.status_code == 404


@pytest.mark.django_db
class TestWorkoutPlanAddExerciseView:
    def url(self, plan_id):
        return reverse("tracker:plan_add_exercise", kwargs={"plan_id": plan_id})

    def test_add_exercise_requires_auth(self, client, plan):
        response = client.get(self.url(plan.id))
        assert response.status_code == 302

    def test_add_exercise_get_returns_200(self, auth_client, plan):
        response = auth_client.get(self.url(plan.id))
        assert response.status_code == 200

    def test_add_exercise_post_creates_exercise_set(self, auth_client, plan, exercise):
        auth_client.post(
            self.url(plan.id),
            {
                "exercise_id": exercise.id,
                "sets": "3",
                "reps": "10",
                "weight": "60",
            },
        )
        assert ExerciseSet.objects.filter(workout_plan=plan, exercise=exercise).exists()

    def test_add_exercise_redirects_to_plan_detail(self, auth_client, plan, exercise):
        response = auth_client.post(
            self.url(plan.id),
            {
                "exercise_id": exercise.id,
                "sets": "3",
                "reps": "10",
                "weight": "60",
            },
        )
        assert response.status_code == 302
        assert f"/plans/{plan.id}/" in response["Location"]

    def test_add_exercise_without_exercise_id_shows_error(self, auth_client, plan):
        response = auth_client.post(
            self.url(plan.id),
            {
                "sets": "3",
                "reps": "10",
                "weight": "60",
            },
        )
        assert response.status_code == 302


@pytest.mark.django_db
class TestExerciseSetDeleteView:
    def url(self, es_id):
        return reverse("tracker:exercise_set_delete", kwargs={"es_id": es_id})

    def test_delete_requires_auth(self, client, plan, exercise):
        es = ExerciseSetFactory(workout_plan=plan, exercise=exercise)
        response = client.post(self.url(es.id))
        assert response.status_code == 302

    def test_delete_removes_exercise_set(self, auth_client, plan, exercise):
        es = ExerciseSetFactory(workout_plan=plan, exercise=exercise)
        es_id = es.id
        auth_client.post(self.url(es_id))
        assert not ExerciseSet.objects.filter(id=es_id).exists()
