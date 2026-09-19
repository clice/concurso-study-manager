from django.shortcuts import render
from apps.competitions.models import Competition


def home(request):
    competitions = Competition.objects.order_by("exam_date", "name")
    return render(
        request,
        "core/home.html",
        {
            "competitions": competitions,
            "competition_count": competitions.count(),
        },
    )
