from datetime import timedelta, datetime
from django.db import models
from django.utils.timezone import now
from .models import ShiftRequirement, Shift, Employee, ShiftType

def generate_schedule_for_week(custom_start_date=None):
    if custom_start_date:
        start_date = custom_start_date
    else:
        today = now().date()
        start_date = today - timedelta(days=today.weekday())

    end_date = start_date + timedelta(days=6)

    print(f"\n📅 Generiranje rasporeda od {start_date} do {end_date}\n")

    shifts = []
    employee_hours = {}
    schedule_table = {}

    shift_requirements = ShiftRequirement.objects.filter(date__range=[start_date, end_date])

    if not shift_requirements.exists():
        print("⚠️ Nema shift requirement unosa za ovaj tjedan!")
        return shifts

    for requirement in shift_requirements:
        shift_type = requirement.shift_type
        shift_start = shift_type.start_time
        total_hours_needed = requirement.required_hours

        print(f"\n=== Procesiram {requirement.department.name} za {requirement.date} ({requirement.date.strftime('%A')}) ===")

        available_employees = Employee.objects.filter(
            departments=requirement.department,
            available_days__name=requirement.date.strftime('%A'),
            can_work_shifts=shift_type
        ).exclude(
            timeoff__start_date__lte=requirement.date,
            timeoff__end_date__gte=requirement.date
        ).distinct().order_by('-max_weekly_hours', 'priority')

        print(f"👥 Pronađeno {available_employees.count()} dostupnih radnika")
        print("📜 Lista radnika:", list(available_employees.values_list('user__username', flat=True)))

        if available_employees.count() == 0:
            print(f"⚠️ NEMA DOSTUPNIH RADNIKA ZA {requirement.department.name} na {requirement.date}")
            continue

        assigned_employees = []
        while total_hours_needed > 0 and available_employees.exists():
            employee = available_employees.first()

            assigned_shifts = Shift.objects.filter(
                employee=employee,
                date=requirement.date,
                start_time__lt=shift_type.end_time,
                end_time__gt=shift_type.start_time
            )

            if assigned_shifts.exists():
                print(f"⚠️ {employee.user.username} već ima smjenu na {requirement.date}, preskačem.")
                available_employees = available_employees.exclude(id=employee.id)
                continue

            total_assigned_hours = Shift.objects.filter(
                employee=employee, date__range=[start_date, end_date]
            ).aggregate(total_hours=models.Sum(models.F('end_time') - models.F('start_time')))['total_hours']

            if total_assigned_hours is None:
                total_assigned_hours = 0
            else:
                total_assigned_hours = total_assigned_hours.total_seconds() / 3600

            print(f"⏳ {employee.user.username} trenutno ima {total_assigned_hours:.2f} sati u ovom tjednu.")

            if total_assigned_hours >= employee.max_weekly_hours:
                print(f"❌ {employee.user.username} je dosegao maksimalnih {employee.max_weekly_hours}h")
                available_employees = available_employees.exclude(id=employee.id)
                continue

            remaining_weekly_hours = employee.max_weekly_hours - total_assigned_hours
            daily_max = min(employee.max_daily_hours, remaining_weekly_hours, total_hours_needed)

            if daily_max <= 0:
                print(f"⚠️ {employee.user.username} ne može raditi više sati ovaj tjedan.")
                available_employees = available_employees.exclude(id=employee.id)
                continue

            shift_end_time = (datetime.combine(requirement.date, shift_start) + timedelta(hours=daily_max)).time()
            shift_end_time = min(shift_end_time, shift_type.end_time)

            if shift_end_time <= shift_start:
                print(f"⛔ Greška! {employee.user.username} dobio bi nevažeću smjenu: {shift_start} - {shift_end_time}")
                available_employees = available_employees.exclude(id=employee.id)
                continue

            shift = Shift(
                employee=employee,
                department=requirement.department,
                role=employee.roles.first(),
                date=requirement.date,
                start_time=shift_start,
                end_time=shift_end_time
            )
            shift.save()
            shifts.append(shift)
            assigned_employees.append(employee.user.username)

            print(f"✅ Dodijeljena smjena: {employee.user.username} {shift_start.strftime('%H:%M')} - {shift_end_time.strftime('%H:%M')}")

            if employee.user.username not in schedule_table:
                schedule_table[employee.user.username] = {d: "-" for d in range(7)}

            schedule_table[employee.user.username][(requirement.date - start_date).days] = f"{shift_start.strftime('%H:%M')} - {shift_end_time.strftime('%H:%M')}"

            employee_hours[employee.user.username] = employee_hours.get(employee.user.username, 0) + daily_max
            total_hours_needed -= daily_max
            shift_start = shift_end_time

            available_employees = available_employees.exclude(id=employee.id)

        print(f"👥 Radnici dodijeljeni za {requirement.date}: {assigned_employees}")

    print("\n📊 **Pregled rasporeda za tjedan** 📊")
    print(f"{'Employee':<15} {'Mon':<10} {'Tue':<10} {'Wed':<10} {'Thu':<10} {'Fri':<10} {'Sat':<10} {'Sun':<10} | Total Hours")
    print("-" * 95)

    for employee, shifts in schedule_table.items():
        shifts_display = " ".join([f"{shifts[d]:<10}" for d in range(7)])
        print(f"{employee:<15} {shifts_display} | {employee_hours[employee]:<5}")

    print("\n✅✅ **Raspored generiran uspješno!** ✅✅")
    return shifts
