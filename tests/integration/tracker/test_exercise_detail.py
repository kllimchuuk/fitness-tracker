import pytest
from django.urls import reverse

from tests.factories.tracker_factories import ExerciseSetFactory
from tests.factories.tracker_factories import WorkoutPlanFactory


def detail_url(exercise_id):
    return reverse("tracker:exercise_detail", kwargs={"exercise_id": exercise_id})


def update_url(exercise_id):
    return reverse("tracker:exercise_update", kwargs={"exercise_id": exercise_id})


@pytest.mark.django_db
class TestRelatedPlansPrivacy:
    @pytest.fixture
    def foreign_plan(self, other_user, exercise):
        plan = WorkoutPlanFactory(creator=other_user, name="Secret Plan")
        ExerciseSetFactory(workout_plan=plan, exercise=exercise)
        return plan

    def test_anonymous_does_not_see_other_users_plans_or_emails(self, client, exercise, foreign_plan, other_user):
        content = client.get(detail_url(exercise.id)).content.decode()
        assert "Secret Plan" not in content
        assert other_user.email not in content

    def test_user_does_not_see_other_users_plans_or_emails(self, auth_client, exercise, foreign_plan, other_user):
        content = auth_client.get(detail_url(exercise.id)).content.decode()
        assert "Secret Plan" not in content
        assert other_user.email not in content

    def test_user_sees_own_plans_with_a_link(self, auth_client, exercise, plan):
        ExerciseSetFactory(workout_plan=plan, exercise=exercise)
        content = auth_client.get(detail_url(exercise.id)).content.decode()
        assert plan.name in content
        assert reverse("tracker:plan_detail", kwargs={"plan_id": plan.id}) in content

    def test_related_plans_section_is_rendered_once(self, auth_client, exercise, plan):
        ExerciseSetFactory(workout_plan=plan, exercise=exercise)
        content = auth_client.get(detail_url(exercise.id)).content.decode()
        assert content.count("Workout Plans Using This Exercise") == 1


@pytest.mark.django_db
class TestManageButtons:
    def test_anonymous_sees_no_manage_controls(self, client, exercise):
        content = client.get(detail_url(exercise.id)).content.decode()
        assert update_url(exercise.id) not in content
        assert "Manage Exercise" not in content

    def test_regular_user_sees_no_manage_controls_on_system_exercise(self, auth_client, exercise):
        content = auth_client.get(detail_url(exercise.id)).content.decode()
        assert update_url(exercise.id) not in content
        assert "Manage Exercise" not in content

    def test_owner_sees_manage_controls_once(self, auth_client, owned_exercise):
        content = auth_client.get(detail_url(owned_exercise.id)).content.decode()
        assert content.count(update_url(owned_exercise.id)) == 1
        assert content.count("Manage Exercise") == 1

    def test_staff_sees_manage_controls_on_system_exercise(self, staff_client, exercise):
        content = staff_client.get(detail_url(exercise.id)).content.decode()
        assert content.count(update_url(exercise.id)) == 1
