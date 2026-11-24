from django import forms

from .models import Exercise
from .models import WorkoutPlan


class ExerciseForm(forms.ModelForm):
    class Meta:
        model = Exercise
        fields = ["name", "type", "primary_muscle", "equipment", "description"]
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
            "primary_muscle": forms.Select(attrs={"class": "search-input"}),
            "equipment": forms.Select(attrs={"class": "search-input"}),
            "description": forms.TextInput(
                attrs={
                    "class": "search-input",
                    "placeholder": "Description",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["primary_muscle"].required = False
        self.fields["equipment"].required = False

    def clean_primary_muscle(self) -> str:
        return self.cleaned_data["primary_muscle"] or self.instance.primary_muscle or Exercise.Muscle.OTHER

    def clean_equipment(self) -> str:
        return self.cleaned_data["equipment"] or self.instance.equipment or Exercise.Equipment.OTHER


class WorkoutPlanForm(forms.ModelForm):
    class Meta:
        model = WorkoutPlan
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "search-input", "placeholder": "Plan name"}),
            "description": forms.Textarea(attrs={"class": "search-input", "placeholder": "Plan description", "rows": 3}),
        }
