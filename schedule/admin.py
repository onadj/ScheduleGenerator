from django.contrib import admin  # Ovo MORA biti prvo!
from django.utils.timezone import now
from .models import Department, Role, Employee, ShiftRequirement, Shift, TimeOff, Day, ShiftType
from .utils import generate_schedule_for_week


# Django admin setup
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(ShiftType)
class ShiftTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time')

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'max_weekly_hours', 'max_daily_hours')
    filter_horizontal = ('departments', 'roles', 'available_days', 'can_work_shifts')

@admin.register(ShiftRequirement)
class ShiftRequirementAdmin(admin.ModelAdmin):
    list_display = ('department', 'date', 'shift_type', 'required_hours')

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('employee', 'department', 'role', 'date', 'start_time', 'end_time')

@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'reason')

# Generiranje rasporeda - premješteno u utils.py u schedule_app
from django.utils.timezone import now
from .utils import generate_schedule_for_week

@admin.action(description="Generate schedule for current week")
def generate_schedule(modeladmin, request, queryset):
    start_date = now().date()
    generate_schedule_for_week(start_date)

ShiftRequirementAdmin.actions = [generate_schedule]
