# Generated by Django 4.2 on 2024-09-07 18:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0021_remove_session_activities_session_activities'),
    ]

    operations = [
        migrations.RenameField(
            model_name='session',
            old_name='activities',
            new_name='note',
        ),
    ]
