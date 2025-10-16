from django import forms

from .models import Exercise


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
