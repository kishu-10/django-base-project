from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveAPIView,
    RetrieveUpdateAPIView,
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.views import TokenObtainPairView
from helpers.viewsets import CustomModelViewSet

from user.serializers import CustomTokenObtainPairSerializer

from .models import (
    Menu,
    Privilege,
    Role,
)
from .serializers import *
from rest_framework import filters

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class MenuListView(ListAPIView):
    queryset = Menu.objects.filter(is_active=True).order_by("order_id")
    serializer_class = MenuSerializer


class RoleViewSet(CustomModelViewSet):
    serializer_class = RoleSerializer
    queryset = Role.objects.order_by("-id")
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "code"]


class PrivilegeListView(ListAPIView):
    serializer_class = PrivilegeSerializer
    queryset = Privilege.objects.filter(is_active=True)
