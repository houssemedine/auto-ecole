# Generated by Django 4.0.5 on 2022-07-03 15:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('autoecole_api', '0004_alter_school_options_alter_school_adress_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='school',
            old_name='mail',
            new_name='email',
        ),
        migrations.CreateModel(
            name='Card',
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
                ('licence_type', models.CharField(max_length=50)),
                ('start_at', models.DateField()),
                ('end_at', models.DateField()),
                ('result', models.CharField(default='In progress', max_length=50)),
                ('price', models.DecimalField(decimal_places=2, max_digits=5)),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='autoecole_api.student')),
            ],
            options={
                'ordering': ['licence_type'],
            },
        ),
    ]