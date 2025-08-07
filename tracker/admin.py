from django.contrib import admin

# Register your models here.
from .models import (Admin, Combination, Customer, Exercise, Result, User,
                     WeightTracker, WorkoutPlan, WorkoutSession)

admin.site.register(User)
admin.site.register(Customer)
admin.site.register(Admin)
admin.site.register(Exercise)
admin.site.register(Combination)
admin.site.register(WorkoutPlan)
admin.site.register(WorkoutSession)
admin.site.register(WeightTracker)
admin.site.register(Result)
