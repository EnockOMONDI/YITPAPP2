from django.db import migrations
import pyuploadcare.dj.models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0005_lesson_audio_url_lesson_document_url_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='thumbnail',
            field=pyuploadcare.dj.models.ImageField(blank=True, null=True),
        ),
    ]
