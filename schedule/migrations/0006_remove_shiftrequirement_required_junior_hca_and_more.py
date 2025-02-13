# Generated by Django 5.1.6 on 2025-02-07 10:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0005_shiftrequirement_required_junior_hca_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shiftrequirement',
            name='required_junior_hca',
        ),
        migrations.RemoveField(
            model_name='shiftrequirement',
            name='required_junior_nurses',
        ),
        migrations.RemoveField(
            model_name='shiftrequirement',
            name='required_senior_hca',
        ),
        migrations.RemoveField(
            model_name='shiftrequirement',
            name='required_senior_nurses',
        ),
        migrations.AddField(
            model_name='role',
            name='department',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='schedule.department'),
        ),
        migrations.AddField(
            model_name='shifttype',
            name='duration_hours',
            field=models.PositiveIntegerField(default=8),
        ),
        migrations.AlterField(
            model_name='shifttype',
            name='end_time',
            field=models.TimeField(),
        ),
        migrations.AlterField(
            model_name='shifttype',
            name='start_time',
            field=models.TimeField(),
        ),
    ]
