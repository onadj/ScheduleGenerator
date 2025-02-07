from django.contrib import admin
import csv
import pandas as pd
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
from django.utils.module_loading import import_string
from .models import Department, Role, Employee, ShiftRequirement, Shift, TimeOff, Day, ShiftType

# Dinamički import funkcije generiranja rasporeda
generate_schedule_for_day = import_string("schedule.utils.generate_schedule_for_day")

### 📌 Employee Admin ###
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'user', 'max_weekly_hours', 'max_daily_hours', 'get_departments', 'get_roles', 'priority')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'departments__name', 'roles__name')
    list_filter = ('departments', 'roles', 'available_days', 'can_work_shifts')
    filter_horizontal = ('departments', 'roles', 'available_days', 'can_work_shifts')
    ordering = ('priority', '-max_weekly_hours')

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_full_name.short_description = "Full Name"

    def get_departments(self, obj):
        return ", ".join([d.name for d in obj.departments.all()])
    get_departments.short_description = "Departments"

    def get_roles(self, obj):
        return ", ".join([r.name for r in obj.roles.all()])
    get_roles.short_description = "Roles"

### 📌 ShiftRequirement Admin ###
@admin.register(ShiftRequirement)
class ShiftRequirementAdmin(admin.ModelAdmin):
    list_display = ('department', 'date', 'required_hours', 'get_shift_types', 'get_roles')
    search_fields = ('department__name', 'date', 'required_roles__name')
    list_filter = ('department', 'date')
    ordering = ('date', 'department')
    actions = ['generate_schedule_for_selected']
    filter_horizontal = ('shift_types', 'required_roles')

    def get_shift_types(self, obj):
        return ", ".join([s.name for s in obj.shift_types.all()])
    get_shift_types.short_description = "Shift Types"

    def get_roles(self, obj):
        return ", ".join([r.name for r in obj.required_roles.all()])
    get_roles.short_description = "Required Roles"

    @admin.action(description="✅ Generate schedule for selected shifts")
    def generate_schedule_for_selected(self, request, queryset):
        for requirement in queryset:
            generate_schedule_for_day(requirement.date)
        self.message_user(request, "✅ Schedule generated for the selected shifts.")

### 📌 Shift Admin ###
@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('get_employee_full_name', 'department', 'get_role_name', 'date', 'start_time', 'end_time', 'calculate_total_hours')
    search_fields = ('employee__user__username', 'employee__user__first_name', 'employee__user__last_name', 'department__name', 'role__name', 'date')
    list_filter = ('department', 'role', 'date')
    ordering = ('date', 'start_time')
    actions = ['export_schedule_to_csv', 'export_schedule_to_excel', 'export_schedule_to_pdf', 'delete_all_shifts']

    def get_employee_full_name(self, obj):
        return f"{obj.employee.user.first_name} {obj.employee.user.last_name} ({obj.employee.user.username})"
    get_employee_full_name.short_description = "Employee"

    def get_role_name(self, obj):
        return obj.role.name
    get_role_name.short_description = "Role"

    def calculate_total_hours(self, obj):
        start_dt = datetime.combine(obj.date, obj.start_time)
        end_dt = datetime.combine(obj.date, obj.end_time)

        # Ako se smjena proteže preko ponoći, dodaj jedan dan na end_dt
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)

        total_seconds = (end_dt - start_dt).total_seconds()
        return max(round(total_seconds / 3600, 2), 0)  # Osiguravamo da nema negativnih vrijednosti

    calculate_total_hours.short_description = "Total Hours"

    @admin.action(description="📄 Export schedule to CSV")
    def export_schedule_to_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="schedule.csv"'
        writer = csv.writer(response)
        writer.writerow(['Employee', 'Department', 'Role', 'Date', 'Start Time', 'End Time', 'Total Hours'])

        for shift in queryset.distinct():
            writer.writerow([
                self.get_employee_full_name(shift),
                shift.department.name, 
                shift.role.name, 
                shift.date, 
                shift.start_time.strftime('%H:%M'), 
                shift.end_time.strftime('%H:%M'), 
                self.calculate_total_hours(shift)
            ])
        return response

    @admin.action(description="📊 Export schedule to Excel")
    def export_schedule_to_excel(self, request, queryset):
        df = pd.DataFrame([
            (
                self.get_employee_full_name(shift),
                shift.department.name, 
                shift.role.name, 
                shift.date, 
                shift.start_time.strftime('%H:%M'), 
                shift.end_time.strftime('%H:%M'), 
                self.calculate_total_hours(shift)
            ) for shift in queryset.distinct()
        ], columns=['Employee', 'Department', 'Role', 'Date', 'Start Time', 'End Time', 'Total Hours'])

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="schedule.xlsx"'
        df.to_excel(response, index=False)
        return response

    @admin.action(description="📄 Export schedule to PDF")
    def export_schedule_to_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="schedule.pdf"'
        pdf = canvas.Canvas(response, pagesize=letter)
        pdf.setFont("Helvetica", 12)
        y = 750  

        pdf.drawString(200, y, "Generated Schedule")
        y -= 30

        headers = ['Employee', 'Department', 'Role', 'Date', 'Start Time', 'End Time', 'Total Hours']
        x_positions = [50, 150, 250, 350, 450, 500, 550]

        for x, header in zip(x_positions, headers):
            pdf.drawString(x, y, header)
        y -= 20

        for shift in queryset.distinct():
            data = [
                self.get_employee_full_name(shift),
                shift.department.name, 
                shift.role.name, 
                str(shift.date), 
                shift.start_time.strftime('%H:%M'), 
                shift.end_time.strftime('%H:%M'), 
                str(self.calculate_total_hours(shift))
            ]
            for x, value in zip(x_positions, data):
                pdf.drawString(x, y, value)
            y -= 20

            if y < 50:
                pdf.showPage()
                y = 750

        pdf.save()
        return response

    @admin.action(description="🗑 Delete all shifts")
    def delete_all_shifts(self, request, queryset):
        queryset.delete()
        self.message_user(request, "🗑 All selected shifts have been deleted.")

### 📌 Registering other models ###
admin.site.register(Department)
admin.site.register(Role)
admin.site.register(Day)
admin.site.register(ShiftType)
