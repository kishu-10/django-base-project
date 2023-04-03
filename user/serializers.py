from .models import (
    Privilege,
    Role,
    Menu,
)
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
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


class PrivilegeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Privilege
        fields = ["id", "name", "code", "is_active"]


class RoleSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()
    name = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=Role.objects.all(),
                lookup="iexact",
                message="Role name should be unique.",
            )
        ]
    )

    class Meta:
        model = Role
        fields = ["id", "name", "code", "is_active", "users"]


class MenuSerializer(serializers.ModelSerializer):
    privilege = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = [
            "id",
            "name",
            "code",
            "is_active",
            "parent",
            "order_id",
            "url",
            "icon",
            "privilege",
        ]

    def get_privilege(self, obj):
        privileges = obj.privilege.all()
        return PrivilegeSerializer(privileges, many=True).data
