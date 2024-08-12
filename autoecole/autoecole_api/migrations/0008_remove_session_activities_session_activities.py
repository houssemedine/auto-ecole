# Generated by Django 4.0.5 on 2024-07-05 21:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0007_alter_student_tel'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='session',
            name='activities',
        ),
        migrations.AddField(
            model_name='session',
            name='activities',
            field=models.ManyToManyField(to='autoecole_api.activity'),
        ),
    ]