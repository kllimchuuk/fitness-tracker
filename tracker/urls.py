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
    path("plans/", views.WorkoutPlanListView.as_view(), name="plans_list"),
    path("plans/<int:plan_id>/", views.WorkoutPlanDetailView.as_view(), name="plan_detail"),
    path("plans/create/", views.WorkoutPlanCreateView.as_view(), name="plan_create"),
    path("plans/<int:plan_id>/update/", views.WorkoutPlanUpdateView.as_view(), name="plan_update"),
    path("plans/<int:plan_id>/delete/", views.WorkoutPlanDeleteView.as_view(), name="plan_delete"),
    path("exercise-sets/<int:es_id>/delete/", views.ExerciseSetDeleteView.as_view(), name="exercise_set_delete"),
    path("plans/<int:plan_id>/add-exercise/", views.WorkoutPlanAddExerciseView.as_view(), name="plan_add_exercise"),
]
