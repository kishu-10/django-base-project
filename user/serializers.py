from .models import (
    AuthUser,
    InternalUser,
    InstitutionUser,
    IndividualUser,
    Privilege,
    Role,
    Menu,
    RoleMenuPrivilege,
    UserMenuPrivilege,
)
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate_username(self, value):
        try:
            return User.objects.get(
                Q(email=value) | Q(username=value) | Q(mobile_number=value)
            ).username
        except Exception:
            return value

    def validate(self, attrs):
        data = super().validate(attrs)
        data["uuid"] = self.user.uuid
        data["email"] = self.user.email
        data["mobile_number"] = self.user.mobile_number
        data["message"] = "Login Successful"
        return data
