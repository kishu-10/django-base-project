from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoleViewSet, InitAPI

router = DefaultRouter(trailing_slash=False)
router.register("role", RoleViewSet, basename="role-CRUD")

urlpatterns = [
    path("", include(router.urls)),
    path("init", InitAPI.as_view(), name="init_api"),
]
