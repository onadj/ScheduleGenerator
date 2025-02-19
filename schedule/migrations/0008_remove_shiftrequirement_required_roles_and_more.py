# Generated by Django 5.1.6 on 2025-02-07 10:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0007_alter_role_department_alter_shifttype_duration_hours'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shiftrequirement',
            name='required_roles',
        ),
        migrations.RemoveField(
            model_name='shiftrequirement',
            name='shift_type',
        ),
        migrations.AddField(
            model_name='shiftrequirement',
            name='shift_types',
            field=models.ManyToManyField(to='schedule.shifttype'),
        ),
    ]
