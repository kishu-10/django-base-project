from user.utils import (
    get_role_menu_privileges,
    get_menu_modules,
    get_user_parent_menus,
)
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
from helpers.serializers import DynamicFieldsModelSerializer

User = get_user_model()


class AuthUserSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "mobile_number",
        ]


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


class InitMenuSerializer(serializers.ModelSerializer):
    privilege = serializers.SerializerMethodField()
    modules = serializers.SerializerMethodField()

    class Meta:
        model = Menu
        fields = [
            "id",
            "name",
            "code",
            "url",
            "icon",
            "privilege",
            "modules",
        ]

    def get_modules(self, obj):
        request = self.context.get("request")
        modules = Menu.objects.filter(is_active=True, parent=obj).order_by("order_id")
        if not request.user.is_superuser:
            modules = get_menu_modules(request.user, obj)

        serializer = InitMenuSerializer(
            modules, many=True, context={"request": request}
        )
        return serializer.data

    def get_privilege(self, obj):
        request = self.context.get("request")
        return get_role_menu_privileges(request.user, obj)


class InitUserSerializer(serializers.ModelSerializer):
    """serializer for listing user's all the menus"""

    user = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["user", "permissions"]

    def get_user(self, obj):
        return AuthUserSerializer(obj).data

    def get_permissions(self, obj):
        request = self.context.get("request")
        menus = get_user_parent_menus(request.user)
        return InitMenuSerializer(menus, many=True, context={"request": request}).data
