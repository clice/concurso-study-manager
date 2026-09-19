from django.urls import path

from . import views

urlpatterns = [
    path("", views.global_question_list, name="list"),
    path("dashboard/", views.global_question_dashboard, name="dashboard"),
    path(
        "nova/",
        views.global_question_choose_competition,
        name="choose_competition",
    ),
]
