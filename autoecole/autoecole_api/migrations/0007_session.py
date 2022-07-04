# Generated by Django 4.0.5 on 2022-07-04 21:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0006_activity'),
    ]

    operations = [
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('created_by', models.CharField(default='Ibiza', max_length=30)),
                ('updated_by', models.CharField(default='Ibiza', max_length=30)),
                ('is_deleted', models.BooleanField(default=False)),
                ('deleted_by', models.CharField(blank=True, max_length=30, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, null=True)),
                ('restored_at', models.DateTimeField(blank=True, null=True)),
                ('restored_by', models.CharField(blank=True, max_length=30, null=True)),
                ('day', models.DateField()),
                ('start_at', models.TimeField()),
                ('end_at', models.TimeField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=5)),
                ('activity', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='autoecole_api.activity')),
            ],
            options={
                'ordering': ['day'],
            },
        ),
    ]
