from rest_framework.permissions import BasePermission, SAFE_METHODS
from user.models import Menu
from user.utils import get_user_menu_right, check_general_permission


class CustomBasePermission(BasePermission):
    """
    custom base permission class
    """

    module = None

    def has_permission(self, request, view):
        queryset = self.get_queryset(request)
        return check_general_permission(request, queryset)

    def get_queryset(self, request):
        return get_user_menu_right(request.user, self.module)


class ReadOnly(BasePermission):

    edit_methods = ("GET", "PUT", "PATCH", "DELETE")

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        check_predefined = obj.predefined
        if check_predefined == True and obj.created_by != request.user:
            if request.method in SAFE_METHODS:
                return True
        elif check_predefined == False and obj.created_by == request.user:
            return request.method in self.edit_methods
