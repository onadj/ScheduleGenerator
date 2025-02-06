from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import now
import csv
import pandas as pd
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.urls import path
from .models import Department, Role, Employee, ShiftRequirement, Shift, TimeOff, Day, ShiftType
from .utils import generate_schedule_for_week

### 📌 Department ###
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

### 📌 Role ###
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

### 📌 Day ###
@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ('name',)

### 📌 ShiftType ###
@admin.register(ShiftType)
class ShiftTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time')
    search_fields = ('name',)
    list_filter = ('start_time', 'end_time')
    ordering = ('start_time',)

### 📌 Employee ###
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'user', 'max_weekly_hours', 'max_daily_hours', 'get_departments', 'get_roles')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'departments__name', 'roles__name')
    list_filter = ('departments', 'roles', 'available_days', 'can_work_shifts')
    filter_horizontal = ('departments', 'roles', 'available_days', 'can_work_shifts')

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = "Full Name"

    def get_departments(self, obj):
        return ", ".join([d.name for d in obj.departments.all()])
    get_departments.short_description = "Departments"

    def get_roles(self, obj):
        return ", ".join([r.name for r in obj.roles.all()])
    get_roles.short_description = "Roles"

### 📌 ShiftRequirement ###
@admin.register(ShiftRequirement)
class ShiftRequirementAdmin(admin.ModelAdmin):
    list_display = ('department', 'date', 'shift_type', 'required_hours', 'required_senior_nurses', 'required_junior_nurses', 'required_senior_hca', 'required_junior_hca')
    search_fields = ('department__name', 'date', 'shift_type__name')
    list_filter = ('department', 'date', 'shift_type')
    ordering = ('date', 'department')
    actions = ['generate_schedule_for_selected']

    def get_weekday(self, obj):
        return obj.date.strftime('%A')
    get_weekday.short_description = "Weekday"

    @admin.action(description="Generate schedule for selected shifts")
    def generate_schedule_for_selected(self, request, queryset):
        for shift_req in queryset:
            generate_schedule_for_week(shift_req.date)
        self.message_user(request, "Schedule generated for selected shifts.")

### 📌 Shift ###
@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('get_employee_full_name', 'department', 'role', 'date', 'get_weekday', 'start_time', 'end_time', 'calculate_total_hours')
    search_fields = ('employee__user__username', 'employee__user__first_name', 'employee__user__last_name', 'department__name', 'role__name', 'date')
    list_filter = ('department', 'role', 'date')
    ordering = ('date', 'start_time')
    actions = ['export_schedule_to_csv', 'export_schedule_to_excel', 'export_schedule_to_pdf']

    def get_employee_full_name(self, obj):
        return f"{obj.employee.user.first_name} {obj.employee.user.last_name}"
    get_employee_full_name.short_description = "Employee"

    def get_weekday(self, obj):
        return obj.date.strftime('%A')
    get_weekday.short_description = "Weekday"

    def calculate_total_hours(self, obj):
        total_seconds = (obj.end_time.hour * 3600 + obj.end_time.minute * 60) - \
                        (obj.start_time.hour * 3600 + obj.start_time.minute * 60)
        return round(total_seconds / 3600, 2)
    calculate_total_hours.short_description = "Total Hours"

    @admin.action(description="📄 Export schedule to CSV")
    def export_schedule_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="schedule.csv"'
        writer = csv.writer(response)
        writer.writerow(['Employee', 'Department', 'Role', 'Date', 'Weekday', 'Start Time', 'End Time', 'Total Hours'])

        for shift in queryset:
            writer.writerow([shift.get_employee_full_name(), shift.department.name, shift.role.name,
                             shift.date, shift.get_weekday(), shift.start_time, shift.end_time, shift.calculate_total_hours()])
        return response

    @admin.action(description="📊 Export schedule to Excel")
    def export_schedule_to_excel(self, request, queryset):
        df = pd.DataFrame(
            [(s.get_employee_full_name(), s.department.name, s.role.name, s.date, s.get_weekday(), s.start_time, s.end_time, s.calculate_total_hours()) for s in queryset],
            columns=['Employee', 'Department', 'Role', 'Date', 'Weekday', 'Start Time', 'End Time', 'Total Hours']
        )
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="schedule.xlsx"'
        df.to_excel(response, index=False)
        return response

### 📌 TimeOff ###
@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'reason')
    search_fields = ('employee__user__username', 'reason')
    list_filter = ('reason',)
