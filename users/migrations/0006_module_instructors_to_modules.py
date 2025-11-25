from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def populate_module_assignments(apps, schema_editor):
    ModuleInstructor = apps.get_model('users', 'ModuleInstructor')
    Module = apps.get_model('courses', 'Module')

    assignments = list(ModuleInstructor.objects.all())
    for assignment in assignments:
        course = getattr(assignment, 'course', None)
        if not course:
            assignment.delete()
            continue

        modules = list(Module.objects.filter(course_id=course.id))
        if not modules:
            assignment.delete()
            continue

        first = True
        for module in modules:
            if first:
                assignment.module = module
                assignment.course = course
                assignment.save(update_fields=['module', 'course'])
                first = False
            else:
                ModuleInstructor.objects.create(
                    module=module,
                    course=course,
                    instructor=assignment.instructor,
                    assignment_role=assignment.assignment_role,
                    can_edit_content=assignment.can_edit_content,
                    can_manage_enrollments=assignment.can_manage_enrollments,
                    can_grade_assessments=assignment.can_grade_assessments,
                    can_view_analytics=assignment.can_view_analytics,
                    can_communicate_students=assignment.can_communicate_students,
                    can_publish_course=assignment.can_publish_course,
                    assigned_by=assignment.assigned_by,
                    is_active=assignment.is_active,
                    notes=assignment.notes,
                )

    # Ensure every module has the primary course instructor assigned
    for module in Module.objects.select_related('course__instructor'):
        course = module.course
        if not course or not course.instructor_id:
            continue
        ModuleInstructor.objects.get_or_create(
            module=module,
            instructor=course.instructor,
            defaults={
                'assignment_role': 'primary_instructor',
                'assigned_by': course.instructor,
                'can_edit_content': True,
                'can_manage_enrollments': True,
                'can_grade_assessments': True,
                'can_view_analytics': True,
                'can_communicate_students': True,
                'can_publish_course': True,
                'is_active': True,
                'course': course,
            }
        )
        # get_or_create above ensures existing entries updated? if existing but lacking module?
        # For completeness, ensure course is set for entries created via defaults.
        ModuleInstructor.objects.filter(
            module=module,
            instructor=course.instructor,
            course__isnull=True
        ).update(course=course)
    # Remove any null course assignments before dropping the field.
    for assignment in ModuleInstructor.objects.filter(course__isnull=True).select_related('module__course'):
        module = assignment.module
        if module and module.course_id:
            assignment.course = module.course
            assignment.save(update_fields=['course'])


def noop_reverse(apps, schema_editor):
    # Irreversible migration
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('courses', '0006_course_thumbnail_uploadcare'),
        ('users', '0005_add_trial_system_fields'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='CourseInstructor',
            new_name='ModuleInstructor',
        ),
        migrations.AlterModelOptions(
            name='moduleinstructor',
            options={'ordering': ['-assigned_at'], 'verbose_name': 'Module Instructor Assignment', 'verbose_name_plural': 'Module Instructor Assignments'},
        ),
        migrations.AlterUniqueTogether(
            name='moduleinstructor',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='moduleinstructor',
            name='module',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='module_instructors', to='courses.module'),
        ),
        migrations.AlterField(
            model_name='moduleinstructor',
            name='instructor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='module_assignments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='moduleinstructor',
            name='assigned_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='module_instructor_assignments_made', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(populate_module_assignments, noop_reverse),
        migrations.RemoveField(
            model_name='moduleinstructor',
            name='course',
        ),
        migrations.AlterField(
            model_name='moduleinstructor',
            name='module',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='module_instructors', to='courses.module'),
        ),
        migrations.AlterUniqueTogether(
            name='moduleinstructor',
            unique_together={('module', 'instructor')},
        ),
    ]
