from django.http import JsonResponse
from django.utils.timezone import now
from .utils import generate_schedule_for_day  # ⬅️ ISPRAVNO: Import bez pozivanja funkcije

def generate_schedule_view(request):
    start_date = now().date()
    shifts = generate_schedule_for_day(start_date)  # ⬅️ Sada pozivamo funkciju unutar view-a
    return JsonResponse({"shifts_created": len(shifts)})
