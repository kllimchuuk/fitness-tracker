# Generated manually for User model migration

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0001_initial"),
        ("tracker", "0001_initial"),
    ]

    operations = [
        # Remove workout_plans field from User model
        migrations.RemoveField(
            model_name="user",
            name="workout_plans",
        ),
        # Delete the old User model
        migrations.DeleteModel(
            name="User",
        ),
        # Update ForeignKey references to use settings.AUTH_USER_MODEL
        migrations.AlterField(
            model_name="weighttracker",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name="workoutplan",
            name="creator",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name="workoutsession",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
