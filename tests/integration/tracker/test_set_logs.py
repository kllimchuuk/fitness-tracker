import pytest
from django.db import IntegrityError
from django.db import transaction
from django.db.models import ProtectedError

from tests.factories.tracker_factories import ExerciseFactory
from tests.factories.tracker_factories import SetLogFactory
from tests.factories.tracker_factories import WorkoutSessionFactory
from tracker.models import SetLog
from tracker.service.exceptions import ServiceError
from tracker.service.set_log import list_set_logs
from tracker.service.set_log import log_set


@pytest.mark.django_db
class TestSetLogModel:
    def test_logs_belong_to_session_in_set_order(self, active_session, exercise):
        SetLogFactory(session=active_session, exercise=exercise, set_number=2)
        SetLogFactory(session=active_session, exercise=exercise, set_number=1)
        numbers = [log.set_number for log in active_session.set_logs.all()]
        assert numbers == [1, 2]

    def test_set_number_is_unique_per_session_and_exercise(self, active_session, exercise):
        SetLogFactory(session=active_session, exercise=exercise, set_number=1)
        with pytest.raises(IntegrityError), transaction.atomic():
            SetLogFactory(session=active_session, exercise=exercise, set_number=1)

    def test_same_set_number_allowed_for_another_exercise(self, active_session, exercise):
        SetLogFactory(session=active_session, exercise=exercise, set_number=1)
        SetLogFactory(session=active_session, exercise=ExerciseFactory(), set_number=1)
        assert SetLog.objects.count() == 2

    @pytest.mark.parametrize(
        "field,value",
        [("reps", 0), ("weight_kg", -1.0), ("rpe", 5.5), ("rpe", 10.5)],
    )
    def test_database_rejects_out_of_range_values(self, active_session, exercise, field, value):
        with pytest.raises(IntegrityError), transaction.atomic():
            SetLogFactory(session=active_session, exercise=exercise, **{field: value})

    def test_rpe_is_optional(self, active_session, exercise):
        log = SetLogFactory(session=active_session, exercise=exercise, rpe=None)
        assert log.rpe is None

    def test_exercise_with_logs_cannot_be_deleted(self, exercise):
        SetLogFactory(exercise=exercise)
        with pytest.raises(ProtectedError):
            exercise.delete()

    def test_deleting_session_deletes_its_logs(self, active_session, exercise):
        SetLogFactory(session=active_session, exercise=exercise)
        active_session.delete()
        assert SetLog.objects.count() == 0


@pytest.mark.django_db
class TestLogSet:
    def payload(self, exercise, **extra):
        return {"exercise_id": exercise.id, "reps": 8, "weight_kg": 60.0, **extra}

    def test_logs_a_set_for_own_active_session(self, user, active_session, exercise):
        result = log_set(active_session.id, self.payload(exercise, rpe=8.5), user)
        assert result.set_number == 1
        assert result.reps == 8
        assert result.weight_kg == 60.0
        assert result.rpe == 8.5
        assert result.session_id == active_session.id

    def test_set_numbers_increase_per_exercise(self, user, active_session, exercise):
        first = log_set(active_session.id, self.payload(exercise), user)
        second = log_set(active_session.id, self.payload(exercise), user)
        other = log_set(active_session.id, self.payload(ExerciseFactory()), user)
        assert (first.set_number, second.set_number, other.set_number) == (1, 2, 1)

    def test_own_private_exercise_can_be_logged(self, user, active_session, owned_exercise):
        result = log_set(active_session.id, self.payload(owned_exercise), user)
        assert result.exercise_id == owned_exercise.id

    def test_archived_exercise_can_still_be_logged(self, user, active_session):
        archived = ExerciseFactory(archived_at="2026-01-01T00:00:00Z")
        result = log_set(active_session.id, self.payload(archived), user)
        assert result.exercise_id == archived.id

    def test_another_users_session_is_404(self, user, exercise):
        foreign = WorkoutSessionFactory(status="active")
        with pytest.raises(ServiceError) as error:
            log_set(foreign.id, self.payload(exercise), user)
        assert error.value.code == 404

    def test_invisible_exercise_is_404(self, user, active_session, other_exercise):
        with pytest.raises(ServiceError) as error:
            log_set(active_session.id, self.payload(other_exercise), user)
        assert error.value.code == 404

    def test_completed_session_is_400(self, user, completed_session, exercise):
        with pytest.raises(ServiceError) as error:
            log_set(completed_session.id, self.payload(exercise), user)
        assert error.value.code == 400

    @pytest.mark.parametrize("missing", ["exercise_id", "reps", "weight_kg"])
    def test_missing_required_field_is_400(self, user, active_session, exercise, missing):
        payload = self.payload(exercise)
        del payload[missing]
        with pytest.raises(ServiceError) as error:
            log_set(active_session.id, payload, user)
        assert error.value.code == 400
        assert missing in str(error.value)

    @pytest.mark.parametrize(
        "extra",
        [{"reps": 0}, {"reps": "8"}, {"weight_kg": -1}, {"weight_kg": "heavy"}, {"rpe": 5}, {"rpe": 11}],
    )
    def test_out_of_range_or_wrong_type_is_400(self, user, active_session, exercise, extra):
        with pytest.raises(ServiceError) as error:
            log_set(active_session.id, self.payload(exercise, **extra), user)
        assert error.value.code == 400
        assert SetLog.objects.count() == 0

    def test_booleans_are_not_numbers(self, user, active_session, exercise):
        with pytest.raises(ServiceError) as error:
            log_set(active_session.id, self.payload(exercise, reps=True), user)
        assert error.value.code == 400


@pytest.mark.django_db
class TestListSetLogs:
    def test_lists_logs_of_own_session_in_order(self, user, active_session, exercise):
        SetLogFactory(session=active_session, exercise=exercise, set_number=2)
        SetLogFactory(session=active_session, exercise=exercise, set_number=1)
        result = list_set_logs(active_session.id, user)
        assert [log.set_number for log in result] == [1, 2]

    def test_another_users_session_is_404(self, user):
        foreign = WorkoutSessionFactory()
        with pytest.raises(ServiceError) as error:
            list_set_logs(foreign.id, user)
        assert error.value.code == 404
