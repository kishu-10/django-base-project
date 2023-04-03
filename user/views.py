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
    queryset = Menu.objects.all()
    serializer_class = MenuSerializer


class RoleCreateView(APIView):
    def post(self, request, format=None):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            # create_log
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleListView(ListAPIView):
    serializer_class = RoleSerializer
    queryset = Role.objects.all().order_by("-id")
    filter_backends = [filters.SearchFilter]
    search_fields = ["name", "code"]


class RoleDetailView(APIView):
    def get(self, request, *args, **kwargs):
        role = get_object_or_404(Role, pk=kwargs.get("id"))
        serializer = RoleSerializer(role)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MenuListView(ListAPIView):
    queryset = Menu.objects.filter(is_active=True).order_by("order_id")
    serializer_class = MenuSerializer


class PrivilegeListView(ListAPIView):
    serializer_class = PrivilegeSerializer
    queryset = Privilege.objects.filter(is_active=True)
