# Generated by Django 4.2 on 2024-10-22 16:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0005_alter_notification_options_student_card_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='card_id',
            field=models.IntegerField(unique=True),
        ),
    ]
