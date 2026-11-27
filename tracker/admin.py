from django.contrib import admin

from .models import Exercise
from .models import ExerciseSet
from .models import SetLog
from .models import WeightTracker
from .models import WorkoutPlan
from .models import WorkoutSession

admin.site.register(WorkoutPlan)
admin.site.register(Exercise)
admin.site.register(ExerciseSet)
admin.site.register(WorkoutSession)
admin.site.register(SetLog)
admin.site.register(WeightTracker)
