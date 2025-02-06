from datetime import timedelta, datetime
from .models import ShiftRequirement, Shift, Employee, Day, ShiftType, TimeOff

def generate_schedule_for_week(start_date):
    end_date = start_date + timedelta(days=6)
    shifts = []

    for requirement in ShiftRequirement.objects.filter(date__range=[start_date, end_date]):
        required_hours = requirement.required_hours
        shift_type = requirement.shift_type  # Dohvati potrebnu smjenu
        shift_start = shift_type.start_time  # Početak smjene iz ShiftType

        # Pronađi radnike koji mogu raditi ovu smjenu
        available_employees = Employee.objects.filter(
            departments=requirement.department,
            roles__in=requirement.required_roles.all(),
            available_days__name=requirement.date.strftime('%A'),
            can_work_shifts=shift_type  # Radnik mora moći raditi ovu smjenu
        ).exclude(
            timeoff__start_date__lte=requirement.date,
            timeoff__end_date__gte=requirement.date
        ).distinct()

        for employee in available_employees:
            if required_hours <= 0:
                break

            employee_role = employee.roles.filter(id__in=requirement.required_roles.all()).first()
            if not employee_role:
                continue  # Preskoči ako radnik nema potrebnu ulogu

            # Poštuj maksimalne dnevne sate
            daily_max = min(employee.max_daily_hours, required_hours)

            # Odredi kraj smjene (ne prelazi kraj shift_type)
            shift_end_time = min(
                (datetime.combine(requirement.date, shift_start) + timedelta(hours=daily_max)).time(),
                shift_type.end_time  # Ne prelazi krajnje vrijeme ShiftType-a
            )

            # Kreiraj smjenu
            shift = Shift(
                employee=employee,
                department=requirement.department,
                role=employee_role,
                date=requirement.date,
                start_time=shift_start,
                end_time=shift_end_time
            )
            shift.save()
            shifts.append(shift)

            # Smanji preostale potrebne sate
            required_hours -= daily_max
            shift_start = shift_end_time

    return shifts
