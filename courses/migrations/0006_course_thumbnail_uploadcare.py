from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_lesson_audio_url_lesson_document_url_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='course',
            name='thumbnail',
        ),
        migrations.AddField(
            model_name='course',
            name='thumbnail_url',
            field=models.URLField(blank=True, help_text='Uploadcare CDN URL for the course image'),
        ),
    ]
