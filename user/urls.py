from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoleViewSet, PrivilegeListView, MenuListView

router = DefaultRouter(trailing_slash=False)
router.register("role", RoleViewSet, basename="role-CRUD")

urlpatterns = [
    path("", include(router.urls)),
    path("privilege", PrivilegeListView.as_view(), name="privilege"),
    path("menu", MenuListView.as_view(), name="menu"),
]
