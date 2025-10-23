from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("exercises/", views.ExerciseListView.as_view(), name="exercises_list"),
    path("exercises/<int:exercise_id>/", views.ExerciseDetailView.as_view(), name="exercise_detail"),
    path("exercises/create/", views.ExerciseCreateView.as_view(), name="exercise_create"),
    path("exercises/<int:exercise_id>/update/", views.ExerciseUpdateView.as_view(), name="exercise_update"),
    path("exercises/<int:exercise_id>/delete/", views.ExerciseDeleteView.as_view(), name="exercise_delete"),
    path("api/exercises/", views.ApiExerciseListView.as_view(), name="api_exercises"),
    path("api/exercises/<int:exercise_id>/", views.ApiExerciseDetailView.as_view(), name="api_exercise_detail"),
]
