from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from helpers.abstract import BaseModel


class AuthUser(AbstractUser):

    first_name = None
    last_name = None
    uuid = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    mobile_number = models.CharField(max_length=15, blank=False, unique=True)
    email = models.EmailField(unique=True)
    is_email_verified = models.BooleanField(default=False)

    created_date = models.DateTimeField(blank=False, auto_now_add=True, null=True)
    updated_date = models.DateTimeField(blank=True, auto_now=True, null=True)
    last_active = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(
        "AuthUser",
        on_delete=models.SET_NULL,
        blank=False,
        null=True,
        related_name="user_created_by",
    )
    updated_by = models.ForeignKey(
        "AuthUser",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="user_updated_by",
    )

    def __str__(self):
        return self.email


class Role(BaseModel):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True, null=True)
    is_active = models.BooleanField(default=True)
    users = models.ManyToManyField(AuthUser, blank=True, related_name="user_roles")

    def __str__(self):
        return self.name


class Privilege(BaseModel):
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Menu(models.Model):
    name = models.CharField(max_length=255)
    name_np = models.CharField(max_length=255)
    code = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="child_menus",
    )
    order_id = models.PositiveSmallIntegerField(null=True, blank=True)
    url = models.CharField(max_length=100, null=True, blank=True)
    privilege = models.ManyToManyField(
        Privilege, related_name="menu_privileges", blank=True
    )
    icon = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.code}"


class RoleMenuPrivilege(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="menu_roles")
    menu = models.ForeignKey(
        Menu, on_delete=models.CASCADE, related_name="roles_privileges"
    )
    privilege = models.ManyToManyField(
        Privilege, blank=True, related_name="role_menu_privileges"
    )
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "{} -> {} -> {}".format(self.role, self.menu, self.is_active)
