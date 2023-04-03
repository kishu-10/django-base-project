import datetime
from rest_framework import serializers
from rest_framework.views import APIView
from .models import AuthUser, InternalUser, Menu, RoleMenuPrivilege, UserMenuPrivilege
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes
from rest_framework.permissions import SAFE_METHODS

account_activation_token = PasswordResetTokenGenerator()
from django.contrib.sites.models import Site


def get_user_menu_right(user, menu):
    if not user.is_superuser:
        try:
            return RoleMenuPrivilege.objects.filter(
                menu=menu, role__users=user
            ).distinct()
        except:
            return RoleMenuPrivilege.objects.filter(menu=menu)


def check_general_permission(request, queryset):
    if request.user.is_superuser:
        return True
    elif request.method in ["PUT", "PATCH"]:
        return queryset.filter(privilege__code="can_update", is_active=True).exists()
    elif request.method == "POST":
        return queryset.filter(privilege__code="can_create", is_active=True).exists()
    elif request.method in SAFE_METHODS and request.user.is_authenticated:
        return queryset.filter(privilege__code="can_read", is_active=True).exists()
    elif request.method == "DELETE":
        return queryset.filter(privilege__code="can_delete", is_active=True).exists()
    else:
        return False


def check_can_read_permissions(privilege_codes):
    if "can_read" in privilege_codes:
        return True
    return False
