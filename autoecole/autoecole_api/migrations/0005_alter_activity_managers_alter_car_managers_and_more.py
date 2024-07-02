# Generated by Django 4.0.5 on 2024-07-02 21:26

import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0004_licencetype_alter_card_licence_type'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='activity',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='car',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='card',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='employee',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='licencetype',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='owner',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='school',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='session',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='student',
            managers=[
                ('undeleted_objects', django.db.models.manager.Manager()),
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AlterField(
            model_name='card',
            name='discount',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=99999999, null=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='hour_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=99999999, null=True),
        ),
        migrations.AlterField(
            model_name='card',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=99999999, null=True),
        ),
    ]
