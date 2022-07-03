# Generated by Django 4.0.5 on 2022-07-03 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0002_alter_school_created_by_alter_school_restored_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='school',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='school',
            name='deleted_by',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='school',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='school',
            name='mail',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='school',
            name='restored_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='school',
            name='restored_by',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name='school',
            name='tel',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]