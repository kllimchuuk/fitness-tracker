from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("exercises/", views.exercises_list, name="exercises_list"),
    path("exercises/<int:exercise_id>/", views.exercise_detail, name="exercise_detail"),
    path("exercises/create/", views.exercise_create, name="exercise_create"),
    path("exercises/<int:exercise_id>/update/", views.exercise_update, name="exercise_update"),
    path("exercises/<int:exercise_id>/delete/", views.exercise_delete, name="exercise_delete"),
    path("api/exercises/", views.api_exercises, name="api_exercises"),
    path("api/exercises/<int:exercise_id>/", views.ApiExerciseDetailView.as_view(), name="api_exercise_detail"),
]
