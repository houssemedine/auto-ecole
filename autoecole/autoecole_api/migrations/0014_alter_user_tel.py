# Generated by Django 4.2 on 2025-06-13 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0013_remove_employee_tel_remove_owner_tel_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='tel',
            field=models.IntegerField(default=900, unique=True),
            preserve_default=False,
        ),
    ]
