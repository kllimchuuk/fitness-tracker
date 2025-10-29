from django import forms

from .models import Exercise
from .models import WorkoutPlan


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ["name", "type", "description"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "search-input",
                    "placeholder": "Name",
                    "required": True,
                }
            ),
            "type": forms.TextInput(
                attrs={
                    "class": "search-input",
                    "placeholder": "Type",
                    "required": True,
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "search-input",
                    "placeholder": "Description",
                }
            ),
        }


class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "search-input", "placeholder": "Plan name"}),
            "description": forms.Textarea(attrs={"class": "search-input", "placeholder": "Plan description", "rows": 3}),
        }
