import json

import pytest

from tests.factories.tracker_factories import ExerciseFactory
from tests.factories.tracker_factories import ExerciseSetFactory
from tests.factories.tracker_factories import SetLogFactory
from tracker.models import Exercise
from tracker.service.exceptions import ServiceError
from tracker.service.exercise import archive_exercise
from tracker.service.exercise import create_exercise
from tracker.service.exercise import delete_exercise
from tracker.service.exercise import get_exercise_by_id
from tracker.service.exercise import unarchive_exercise
from tracker.service.exercise import update_exercise
from tracker.service.exercise_set import add_exercise_set


@pytest.mark.django_db
class TestExerciseMetadata:
    def test_new_exercise_defaults_to_other(self):
        exercise = ExerciseFactory()
        assert exercise.primary_muscle == Exercise.Muscle.OTHER
        assert exercise.equipment == Exercise.Equipment.OTHER

    def test_create_accepts_muscle_and_equipment(self, user):
        payload = {"name": "Bench press", "type": "strength", "primary_muscle": "chest", "equipment": "barbell"}
        created = create_exercise(payload, user)
        assert created.primary_muscle == "chest"
        assert created.equipment == "barbell"

    def test_create_without_metadata_uses_other(self, user):
        created = create_exercise({"name": "Mystery", "type": "strength"}, user)
        assert created.primary_muscle == "other"
        assert created.equipment == "other"

    @pytest.mark.parametrize("field", ["primary_muscle", "equipment"])
    def test_create_rejects_unknown_choice(self, user, field):
        payload = {"name": "Bench press", "type": "strength", field: "nonsense"}
        with pytest.raises(ServiceError) as error:
            create_exercise(payload, user)
        assert error.value.code == 400
        assert field in str(error.value)

    def test_update_changes_metadata(self, user, owned_exercise):
        updated = update_exercise(owned_exercise.id, {"primary_muscle": "back", "equipment": "cable"}, user)
        assert updated.primary_muscle == "back"
        assert updated.equipment == "cable"

    def test_update_rejects_unknown_choice(self, user, owned_exercise):
        with pytest.raises(ServiceError) as error:
            update_exercise(owned_exercise.id, {"equipment": "nonsense"}, user)
        assert error.value.code == 400

    def test_form_page_saves_metadata(self, auth_client, user):
        response = auth_client.post(
            "/exercises/create/",
            {"name": "Row", "type": "strength", "description": "Seated row", "primary_muscle": "back", "equipment": "cable"},
        )
        assert response.status_code == 302
        saved = Exercise.objects.get(name="Row")
        assert (saved.primary_muscle, saved.equipment) == ("back", "cable")

    def test_api_returns_metadata(self, auth_client, owned_exercise):
        response = auth_client.get(f"/api/exercises/{owned_exercise.id}/")
        body = json.loads(response.content)
        assert body["primary_muscle"] == "other"
        assert body["equipment"] == "other"
        assert body["archived_at"] is None


@pytest.mark.django_db
class TestArchiveExercise:
    def test_archiving_sets_timestamp(self, user, owned_exercise):
        result = archive_exercise(owned_exercise.id, user)
        assert result.archived_at is not None
        owned_exercise.refresh_from_db()
        assert owned_exercise.archived_at is not None

    def test_unarchive_clears_timestamp(self, user, owned_exercise):
        archive_exercise(owned_exercise.id, user)
        result = unarchive_exercise(owned_exercise.id, user)
        assert result.archived_at is None

    def test_archived_exercise_stays_visible_and_readable(self, user, owned_exercise):
        archive_exercise(owned_exercise.id, user)
        assert Exercise.objects.visible_to(user).filter(id=owned_exercise.id).exists()
        assert get_exercise_by_id(owned_exercise.id, user).id == owned_exercise.id

    def test_active_excludes_archived(self, user, owned_exercise):
        archive_exercise(owned_exercise.id, user)
        assert not Exercise.objects.visible_to(user).active().filter(id=owned_exercise.id).exists()

    def test_cannot_archive_system_exercise_as_regular_user(self, user, exercise):
        with pytest.raises(ServiceError) as error:
            archive_exercise(exercise.id, user)
        assert error.value.code == 403

    def test_staff_can_archive_system_exercise(self, staff_user, exercise):
        assert archive_exercise(exercise.id, staff_user).archived_at is not None

    def test_invisible_exercise_is_404(self, user, other_exercise):
        with pytest.raises(ServiceError) as error:
            archive_exercise(other_exercise.id, user)
        assert error.value.code == 404

    def test_archived_exercise_cannot_join_a_plan(self, user, plan, owned_exercise):
        archive_exercise(owned_exercise.id, user)
        with pytest.raises(ServiceError) as error:
            add_exercise_set(plan.id, {"exercise_id": owned_exercise.id}, user)
        assert error.value.code == 409

    def test_archived_exercise_already_in_a_plan_can_still_be_updated(self, user, plan, owned_exercise):
        ExerciseSetFactory(workout_plan=plan, exercise=owned_exercise, reps=10)
        archive_exercise(owned_exercise.id, user)
        result = add_exercise_set(plan.id, {"exercise_id": owned_exercise.id, "reps": 12}, user)
        assert result.reps == 12
        assert plan.exerciseset_set.filter(exercise=owned_exercise).count() == 1

    def test_plan_picker_hides_archived(self, auth_client, plan, owned_exercise):
        visible = ExerciseFactory(owner=owned_exercise.owner, name="Visible one")
        archive_exercise(owned_exercise.id, owned_exercise.owner)
        response = auth_client.get(f"/plans/{plan.id}/add-exercise/")
        names = [e.name for e in response.context["exercises"]]
        assert visible.name in names
        assert owned_exercise.name not in names

    def test_delete_of_exercise_with_logs_says_to_archive(self, user, owned_exercise):
        SetLogFactory(exercise=owned_exercise)
        with pytest.raises(ServiceError) as error:
            delete_exercise(owned_exercise.id, user)
        assert error.value.code == 409
        assert "archive" in str(error.value).lower()
