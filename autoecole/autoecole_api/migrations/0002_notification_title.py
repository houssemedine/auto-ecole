# Generated by Django 4.2 on 2024-10-05 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='title',
            field=models.CharField(default='title', max_length=100),
            preserve_default=False,
        ),
    ]