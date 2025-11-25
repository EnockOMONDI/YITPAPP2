from django.db import migrations, models


def rename_content_creator(apps, schema_editor):
    InstructorProfile = apps.get_model('users', 'InstructorProfile')
    InstructorProfile.objects.filter(instructor_role='content_creator').update(instructor_role='content_manager')


def reverse_rename(apps, schema_editor):
    InstructorProfile = apps.get_model('users', 'InstructorProfile')
    InstructorProfile.objects.filter(instructor_role='content_manager').update(instructor_role='content_creator')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_module_instructors_to_modules'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instructorprofile',
            name='instructor_role',
            field=models.CharField(choices=[('system_admin', 'System Administrator'), ('course_instructor', 'Course Instructor'), ('teaching_assistant', 'Teaching Assistant'), ('content_manager', 'Content Manager'), ('accountant', 'Accountant'), ('grader', 'Grader')], default='course_instructor', help_text='Primary instructor role in the system', max_length=30),
        ),
        migrations.RunPython(rename_content_creator, reverse_rename),
    ]
