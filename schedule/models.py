from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
from datetime import timedelta, datetime

# Definicija mogućih dana u tjednu
DAYS_OF_WEEK = [
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
]

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name

class Day(models.Model):
    name = models.CharField(max_length=20, choices=DAYS_OF_WEEK, unique=True)
    
    def __str__(self):
        return self.name

class ShiftType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    start_time = models.TimeField(default="08:00")  # Default vrijeme ako nije unijeto
    end_time = models.TimeField(default="16:00")    # Default kraj smjene

    def __str__(self):
        return f"{self.name} ({self.start_time} - {self.end_time})"


class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    departments = models.ManyToManyField(Department)
    roles = models.ManyToManyField(Role)
    max_weekly_hours = models.PositiveIntegerField()
    available_days = models.ManyToManyField(Day, blank=True)
    max_daily_hours = models.PositiveIntegerField()
    can_work_shifts = models.ManyToManyField(ShiftType, blank=True)
    
    def __str__(self):
        return self.user.username

class ShiftRequirement(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    date = models.DateField()
    shift_type = models.ForeignKey(ShiftType, on_delete=models.CASCADE, default=1)
    required_hours = models.PositiveIntegerField()
    required_roles = models.ManyToManyField(Role)
    
    def __str__(self):
        return f"{self.department.name} - {self.date} {self.shift_type}"

class Shift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    def __str__(self):
        return f"{self.employee.user.username} - {self.department.name} ({self.start_time}-{self.end_time})"

class TimeOff(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255, choices=[('sick', 'Sick'), ('holiday', 'Holiday')])
    
    def __str__(self):
        return f"{self.employee.user.username} - {self.reason} ({self.start_date} to {self.end_date})"