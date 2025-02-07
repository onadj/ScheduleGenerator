from datetime import timedelta, datetime
from django.utils.timezone import now
from django.apps import apps
import random

def generate_schedule_for_day(custom_date):
    ShiftRequirement = apps.get_model('schedule', 'ShiftRequirement')
    Shift = apps.get_model('schedule', 'Shift')
    Employee = apps.get_model('schedule', 'Employee')
    ShiftType = apps.get_model('schedule', 'ShiftType')

    # 🗑️ Obriši sve postojeće smjene prije generiranja novih
    deleted_count, _ = Shift.objects.filter(date=custom_date).delete()
    print(f"🗑️ Obrišeno {deleted_count} smjena za {custom_date}, generiram novi raspored...\n")

    print(f"\n📅 === GENERIRANJE RASPOREDA: {custom_date} ===\n")
    shifts = []
    employee_hours = {}
    assigned_employees = set()

    shift_requirements = ShiftRequirement.objects.filter(date=custom_date)

    if not shift_requirements.exists():
        print("⚠️ Nema ShiftRequirement unosa za ovaj dan!")
        return shifts

    for requirement in shift_requirements:
        total_hours_needed = requirement.required_hours
        assigned_hours = 0  
        full_day_shifts = 0  

        print(f"\n📌 Obrada {requirement.department.name} za {requirement.date.strftime('%A')} ({requirement.date})")
        print(f"📊 Potrebno sati: {total_hours_needed}h")

        allowed_shifts = sorted(requirement.shift_types.all(), key=lambda x: x.start_time)
        print(f"🔍 Dozvoljene smjene: {', '.join([s.name for s in allowed_shifts])}")

        available_employees = list(Employee.objects.filter(
            departments=requirement.department,
            available_days__name=requirement.date.strftime('%A'),
            roles__in=requirement.required_roles.all()
        ).distinct().order_by('-max_weekly_hours', 'priority'))
        random.shuffle(available_employees)

        if not available_employees:
            print("⚠️ NEMA DOSTUPNIH RADNIKA!")
            continue

        shift_employee_map = {}
        for shift_type in allowed_shifts:
            shift_start, shift_end, shift_duration = shift_type.start_time, shift_type.end_time, shift_type.duration_hours

            # **🛑 Ako smo već popunili svih 24h, preskačemo dodatne smjene**
            if assigned_hours >= total_hours_needed:
                assigned_hours = total_hours_needed  
                print(f"❌ Preskačem smjenu {shift_type.name} jer su svi sati popunjeni ({assigned_hours}/{total_hours_needed}).")
                continue  

            print(f"\n🕒 Obrada smjene: {shift_type.name} ({shift_start.strftime('%H:%M')} - {shift_end.strftime('%H:%M')})")

            # ✅ **Ako su već dodijeljene dvije smjene 08-20, preskačemo dodatne smjene**
            if full_day_shifts >= 2:
                assigned_hours = total_hours_needed
                print(f"❌ Preskačem smjenu {shift_type.name} jer su svi sati popunjeni ({assigned_hours}/{total_hours_needed}).")
                continue  

            employees_for_shift = find_available_employees(available_employees, employee_hours, shift_type, assigned_employees, shifts)
            if not employees_for_shift:
                continue  

            max_employees_needed = max(1, (total_hours_needed - assigned_hours) // shift_duration)
            employees_for_shift = employees_for_shift[:max_employees_needed]

            for employee in employees_for_shift:
                if assigned_hours + shift_duration > total_hours_needed:
                    print(f"⚠️ Smjena {shift_start.strftime('%H:%M')} - {shift_end.strftime('%H:%M')} prelazi potreban fond sati! Preskačem.")
                    break  

                shift_key = (shift_start, shift_end)
                if shift_key not in shift_employee_map:
                    shift_employee_map[shift_key] = set()

                if employee not in shift_employee_map[shift_key]:
                    create_shift(employee, requirement, shift_start, shift_end, shift_duration, shifts, employee_hours, assigned_employees)
                    shift_employee_map[shift_key].add(employee)
                    
                    assigned_hours += shift_duration
                    if assigned_hours >= total_hours_needed:
                        assigned_hours = total_hours_needed  
                        break  

                if shift_type.name == "8-20":
                    full_day_shifts += 1

        print(f"\n👥 Radnici dodijeljeni za {requirement.date} ({requirement.department.name}): {', '.join([e.user.username for e in assigned_employees])}")
        print(f"📊 Ukupno sati pokriveno: {total_hours_needed}/{total_hours_needed}")

    print("\n✅✅ **Raspored generiran uspješno!** ✅✅")
    return shifts

# === FUNKCIJE ZA DODJELU SMJENA ===

def find_available_employees(available_employees, employee_hours, shift_type, assigned_employees, shifts):
    shift_duration = shift_type.duration_hours
    selected_employees = []
    
    for employee in available_employees:
        total_assigned_hours = employee_hours.get(employee.user.username, 0)

        if total_assigned_hours >= employee.max_weekly_hours:
            continue

        if any(shift.employee == employee and shift.start_time == shift_type.start_time and shift.end_time == shift_type.end_time for shift in shifts):
            continue
        
        if total_assigned_hours + shift_duration <= employee.max_weekly_hours and employee not in assigned_employees:
            if not check_shift_overlap(employee, shift_type, shifts):
                selected_employees.append(employee)
        
        if len(selected_employees) >= 2:
            break
    return selected_employees

def check_shift_overlap(employee, shift_type, shifts):
    for shift in shifts:
        if shift.employee == employee:
            if not (shift.end_time <= shift_type.start_time or shift.start_time >= shift_type.end_time):
                return True
    return False

def create_shift(employee, requirement, shift_start, shift_end, shift_duration, shifts, employee_hours, assigned_employees):
    Shift = apps.get_model('schedule', 'Shift')

    # 🛑 Sprječavanje duplikata
    existing_shift = Shift.objects.filter(
        employee=employee,
        department=requirement.department,
        date=requirement.date,
        start_time=shift_start,
        end_time=shift_end
    ).exists()

    if existing_shift:
        print(f"⚠️ Smjena već postoji za {employee.user.first_name} {employee.user.last_name} ({employee.user.username}) {shift_start.strftime('%H:%M')} - {shift_end.strftime('%H:%M')}, preskačem!")
        return  # Ako postoji, ne dodaj je ponovo

    # ✅ Ako smjena ne postoji, kreiraj novu
    shift = Shift(
        employee=employee,
        department=requirement.department,
        role=employee.roles.first(),
        date=requirement.date,
        start_time=shift_start,
        end_time=shift_end
    )
    shift.save()
    shifts.append(shift)

    employee_hours[employee.user.username] = employee_hours.get(employee.user.username, 0) + shift_duration
    assigned_employees.add(employee)

    print(f"✅ Dodijeljena smjena: {employee.user.first_name} {employee.user.last_name} ({employee.user.username}) {shift_start.strftime('%H:%M')} - {shift_end.strftime('%H:%M')}")
