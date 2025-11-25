from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_course_thumbnail_uploadcare'),
        ('progress', '0002_add_trial_enrollment_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollment',
            name='last_active_lesson',
            field=models.ForeignKey(blank=True, help_text='Tracks the last lesson the learner interacted with for resume functionality.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='active_enrollments', to='courses.lesson'),
        ),
    ]
