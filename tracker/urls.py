from django.urls import path

from . import views

app_name = "tracker"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("exercises/", views.exercises_list, name="exercises_list"),
    path("exercises/<int:exercise_id>/", views.exercise_detail, name="exercise_detail"),
]
