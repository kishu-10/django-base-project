from .models import Menu, Privilege, RoleMenuPrivilege
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.permissions import SAFE_METHODS

account_activation_token = PasswordResetTokenGenerator()


def get_user_menu_right(user, menu):
    if not user.is_superuser:
        try:
            return RoleMenuPrivilege.objects.filter(
                menu=menu, role__users=user
            ).distinct()
        except:
            return RoleMenuPrivilege.objects.filter(menu=menu)


def get_user_parent_menus(user):
    menus = Menu.objects.filter(is_active=True, parent__isnull=True).order_by(
        "order_id"
    )
    if not user.is_superuser:
        parent_menus = []
        menus = (
            RoleMenuPrivilege.objects.filter(role__users=user)
            .distinct()
            .values_list("menu", flat=True)
        )
        if menus:
            for menu in menus:
                if menu.parent and menu.parent not in parent_menus:
                    parent_menus.append(menu.parent)
                else:
                    parent_menus.append(menu)
        return parent_menus
    else:
        return menus


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


def get_menu_modules(user, parent_menu):
    final_menus = []
    child_menus = Menu.objects.filter(parent=parent_menu).order_by("order_id")
    role_menu_privileges = (
        RoleMenuPrivilege.objects.filter(
            role__users=user,
            privilege__isnull=False,
            menu__is_active=True,
            menu__in=child_menus,
        )
        .distinct()
        .order_by("menu__order_id")
    )
    if role_menu_privileges:
        for menu in role_menu_privileges:
            if check_can_read_permissions(
                menu.privilege.values_list("code", flat=True)
            ):
                final_menus.append(menu.menu)
        final_menus = sorted(final_menus, key=lambda x: x.order_id)
    return final_menus


def get_role_menu_privileges(user, menu):
    response = dict()
    if user.is_superuser:
        privileges = Privilege.objects.all()
        for privilege in privileges:
            response.update({privilege.code: True})
    else:
        role_menu = RoleMenuPrivilege.objects.get(menu=menu, role__users=user)
        for privilege in role_menu.privilege.all():
            response.update({privilege.code: True})
    return response if response else None
