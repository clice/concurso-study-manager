from django.urls import path

from . import views

app_name = "competitions"

urlpatterns = [
    path("novo/", views.competition_create, name="create"),
    path("<int:pk>/", views.competition_detail, name="detail"),
    path("<int:pk>/editar/", views.competition_edit, name="edit"),
    path("<int:pk>/etapas/adicionar/", views.stage_add, name="stage_add"),
    path("<int:pk>/disciplinas/adicionar/", views.discipline_add, name="discipline_add"),
]
