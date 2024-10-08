# Generated by Django 4.2 on 2024-10-06 00:34

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0002_notification_title'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='notification',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='usernotificationpreference',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddField(
            model_name='notification',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='deleted_by',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='notification',
            name='restored_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='restored_by',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usernotificationpreference',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usernotificationpreference',
            name='deleted_by',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usernotificationpreference',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usernotificationpreference',
            name='restored_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usernotificationpreference',
            name='restored_by',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
