# Generated by Django 4.2 on 2024-09-04 17:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0016_alter_card_progress'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='card',
            name='progress',
        ),
    ]
