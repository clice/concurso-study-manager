from django.urls import path

from . import views

app_name = "competitions"

urlpatterns = [
    path("novo/", views.competition_create, name="create"),
    path("<int:pk>/", views.competition_detail, name="detail"),
    path("<int:pk>/editar/", views.competition_edit, name="edit"),
    path("<int:pk>/etapas/adicionar/", views.stage_add, name="stage_add"),
    path("<int:pk>/etapas/<int:stage_id>/editar/", views.stage_edit, name="stage_edit"),
    path("<int:pk>/etapas/reordenar/", views.stage_reorder, name="stage_reorder"),
    path("<int:pk>/disciplinas/adicionar/", views.discipline_add, name="discipline_add"),
    path("<int:pk>/disciplinas/<int:link_id>/editar/", views.discipline_edit, name="discipline_edit"),
    path("<int:pk>/disciplinas/reordenar/", views.discipline_reorder, name="discipline_reorder"),
    path(
        "<int:pk>/edital/<int:link_id>/itens/adicionar/",
        views.syllabus_item_add,
        name="syllabus_item_add",
    ),
    path(
        "<int:pk>/edital/itens/<int:item_id>/editar/",
        views.syllabus_item_edit,
        name="syllabus_item_edit",
    ),
    path(
        "<int:pk>/edital/<int:link_id>/itens/reordenar/",
        views.syllabus_item_reorder,
        name="syllabus_item_reorder",
    ),
]
