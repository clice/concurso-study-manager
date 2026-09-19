from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("concursos/", include("apps.competitions.urls")),
    path("concursos/", include("apps.studies.urls")),
    path("concursos/", include("apps.questions.urls")),
    path("", include("apps.core.urls")),
]
