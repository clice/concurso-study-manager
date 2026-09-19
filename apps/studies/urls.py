from django.urls import path

from . import views

app_name = "studies"

urlpatterns = [
    path("<int:pk>/aulas/", views.lesson_list, name="lesson_list"),
    path(
        "<int:pk>/aulas/nova/",
        views.lesson_choose_discipline,
        name="lesson_choose_discipline",
    ),
    path(
        "<int:pk>/disciplinas/<int:link_id>/aulas/nova/",
        views.lesson_create,
        name="lesson_create",
    ),
    path(
        "<int:pk>/aulas/<int:lesson_id>/editar/",
        views.lesson_edit,
        name="lesson_edit",
    ),
]
