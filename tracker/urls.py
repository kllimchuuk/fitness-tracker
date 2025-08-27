from django.urls import path

from .views import (
    WeightTrackerListView,
    WorkoutPlanUpdateView,
    WorkoutSessionListView,
    index,
    profile,
)


app_name = "tracker"


urlpatterns = [
    path("", index, name="index"),
    path("profile/", profile, name="profile"),
    path("weights/", WeightTrackerListView.as_view(), name="weights"),
    path("sessions/", WorkoutSessionListView.as_view(), name="sessions"),
    path("plans/<int:pk>/edit/", WorkoutPlanUpdateView.as_view(), name="plan_edit"),
]


