from django.urls import path

from . import views

app_name = "questions"

urlpatterns = [
    path("<int:pk>/questoes/", views.question_list, name="question_list"),
    path(
        "<int:pk>/questoes/aulas/",
        views.question_lessons,
        name="question_lessons",
    ),
    path(
        "<int:pk>/questoes/nova/",
        views.question_choose_discipline,
        name="question_choose_discipline",
    ),
    path(
        "<int:pk>/disciplinas/<int:link_id>/questoes/nova/",
        views.question_create,
        name="question_create",
    ),
    path(
        "<int:pk>/questoes/<int:question_id>/",
        views.question_detail,
        name="question_detail",
    ),
    path(
        "<int:pk>/questoes/<int:question_id>/editar/",
        views.question_edit,
        name="question_edit",
    ),
]
