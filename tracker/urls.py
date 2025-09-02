from django.urls import path

from .views import (IndexView, create_workout_plan_view, dashboard_view,
                    start_workout_session_view)

app_name = "tracker"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("workout-plans/create/", create_workout_plan_view, name="workoutplan_create"),
    path(
        "workout-sessions/start/",
        start_workout_session_view,
        name="workoutsession_start",
    ),
]
