# Generated by Django 4.2 on 2025-06-27 19:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0018_alter_sessiontype_options_owner_city'),
    ]

    operations = [
        migrations.AlterField(
            model_name='owner',
            name='city',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='autoecole_api.city'),
        ),
    ]
