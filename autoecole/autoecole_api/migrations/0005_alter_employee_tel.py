# Generated by Django 4.0.5 on 2024-08-17 22:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0004_alter_activity_created_by_alter_activity_deleted_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='tel',
            field=models.IntegerField(default=0, unique=True),
            preserve_default=False,
        ),
    ]