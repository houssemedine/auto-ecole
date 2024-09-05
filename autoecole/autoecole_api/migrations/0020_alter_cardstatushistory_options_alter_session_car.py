# Generated by Django 4.2 on 2024-09-05 20:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0019_remove_card_progress_delete_progress'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cardstatushistory',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterField(
            model_name='session',
            name='car',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='car', to='autoecole_api.car'),
        ),
    ]
