# Generated by Django 4.0.5 on 2024-07-08 08:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0010_rename_result_card_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='card',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='card', to='autoecole_api.card'),
        ),
    ]
