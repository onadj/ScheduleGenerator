from django.http import JsonResponse
from django.utils.timezone import now
from .utils import generate_schedule_for_week

def generate_schedule_view(request):
    start_date = now().date()
    shifts = generate_schedule_for_week(start_date)
    return JsonResponse({"shifts_created": len(shifts)})
