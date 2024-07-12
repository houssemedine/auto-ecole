# Generated by Django 4.0.5 on 2024-07-12 12:11

from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0013_session_car_session_employee'),
    ]

    operations = [
        migrations.CreateModel(
            name='SessionType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.CharField(default='Ibiza', max_length=30)),
                ('updated_by', models.CharField(default='Ibiza', max_length=30)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_by', models.CharField(blank=True, max_length=30, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('restored_at', models.DateTimeField(blank=True, null=True)),
                ('restored_by', models.CharField(blank=True, max_length=30, null=True)),
                ('name', models.CharField(default='Conduite', max_length=50)),
                ('comment', models.CharField(max_length=100)),
            ],
            options={
                'ordering': ['name'],
            },
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
            ],
        ),
    ]
