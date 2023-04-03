import datetime
from email.policy import default
from fileinput import filename
from multiprocessing import context
import numbers
import secrets
from dj_rest_auth.views import PasswordResetConfirmView
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from document_management.utils import export_to_csv, export_to_pdf
from loan_management.models import GuarantorForm, IndividualForm, InstitutionalForm
from loan_management.serializers.individual_serializers import (
    IndividualFormListSerializer,
)
from loan_management.serializers.institution_serializers import (
    InstitutionalFormListSerializer,
)
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
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.views import TokenObtainPairView

from user.serializers import CustomTokenObtainPairSerializer

from .models import (
    AuthUser,
    IndividualUser,
    InstitutionUser,
    InternalUser,
    Menu,
    Privilege,
    Role,
    UserMenuPrivilege,
)
from .serializers import *
from rest_framework import filters
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

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


class RoleUnassignedUsersView(ListAPIView):
    serializer_class = RoleUnassignedUsersSerializer
    queryset = InternalUser.objects.all()
    filter_backends = [filters.SearchFilter]
    pagination_class = None
    search_fields = ["first_name", "middle_name", "last_name", "employee_id"]

    def get_queryset(self):
        role = get_object_or_404(Role, pk=self.kwargs.get("role_id"))
        queryset = super().get_queryset()
        request = self.request
        internal_user = request.user.internal_user
        users_to_exclude = set()
        users_to_exclude.update(role.users.values_list("id", flat=True))
        users_to_exclude.update(
            RoleMenuPrivilege.objects.values_list("role__users", flat=True)
        )
        if request.user.is_superuser or (
            request.user.user_type == "1" and internal_user.branch.is_head_office
        ):
            queryset = InternalUser.objects.exclude(id__in=users_to_exclude).order_by(
                "-id"
            )
        elif request.user.user_type == "1":
            if internal_user.branch.is_province_office:
                queryset = (
                    InternalUser.objects.filter(province=internal_user.branch.province)
                    .exclude(id__in=users_to_exclude)
                    .order_by("-id")
                )
            else:
                queryset = (
                    InternalUser.objects.filter(branch=internal_user.branch)
                    .exclude(id__in=users_to_exclude)
                    .order_by("-id")
                )
        else:
            raise serializers.ValidationError({"message": "Unauthorized"})
        return queryset


class RoleUpdateView(APIView):
    def put(self, request, id, format=None):
        role = get_object_or_404(Role, pk=id)
        prev_role_name = role.name
        serializer = RoleSerializer(role, data=request.data)
        if serializer.is_valid():
            if (
                role.is_active
                and role.users.exists()
                and not serializer.validated_data.get("is_active")
            ):
                raise serializers.ValidationError(
                    {
                        "message": "Role cannot be deleted because it has associated users."
                    }
                )
            obj = serializer.save()
            # create_log
            if prev_role_name != obj.name:
                display_message = f" of Branch {(request.user.internal_user.branch)} updated Role name from {prev_role_name} to {obj.name}."
            else:
                display_message = f" of Branch {(request.user.internal_user.branch)} updated Role, {obj.name}."
            data = {
                "object_id": obj.id,
                "content_type": ContentType.objects.get(model="role"),
                "action_type": "update",
                "display_message": display_message,
            }
            create_internal_user_activity_log(request, data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RoleDeleteView(APIView):
    def delete(self, request, id):
        role = get_object_or_404(Role, pk=id)
        if role.users.exists():
            raise serializers.ValidationError(
                {"message": "Role cannot be deleted because it has associated users."}
            )
        role.is_deleted = True
        role.save()
        # create_log
        display_message = f" of Branch {(request.user.internal_user.branch)} deleted a Role, {role.name}."
        data = {
            "object_id": role.id,
            "content_type": ContentType.objects.get(model="role"),
            "action_type": "delete",
            "display_message": display_message,
        }
        create_internal_user_activity_log(request, data)
        return Response({"message": "Role deleted successfully."})


class MenuListView(ListAPIView):
    queryset = Menu.objects.filter(is_active=True).order_by("order_id")
    serializer_class = MenuSerializer


class PrivilegeListView(ListAPIView):
    serializer_class = PrivilegeSerializer
    queryset = Privilege.objects.filter(is_active=True)


class InitAPI(APIView):
    serializer_class = InitUserSerializer

    def get(self, request, *args, **kwargs):
        serializer = InitUserSerializer(
            self.request.user, many=False, context={"request": request}
        )
        return Response(serializer.data)


class GetMenuPrivilegeView(APIView):
    """
    Get Roles and its respective Privileges for Active Menu
    """

    def get(self, request, *args, **kwargs):
        role = Role.objects.get(pk=self.kwargs.get("pk"))
        role_menu_privilege = RoleMenuPrivilege.objects.filter(
            role=role, is_active=True
        ).order_by("menu__order_id")
        dict_items = dict()
        menus = list()
        # privileges = dict()
        privileges = list()
        for role_menu in role_menu_privilege:
            for privilege in role_menu.privilege.all():
                # privileges.update({
                #     privilege.id: privilege.code
                # })
                privileges.append(privilege.id)
            menus.append(
                {
                    "menu_id": role_menu.menu.id,
                    "menu_code": role_menu.menu.code,
                    "menu_name": role_menu.menu.name,
                    "privilege": privileges,
                }
            )

        dict_items.update(
            {
                "role_id": role.id,
                "role_name": role.name,
                "role_code": role.code,
                "menus": menus,
            }
        )
        return Response(dict_items)


class GetActiveMenuPrivilegeView(APIView):
    def get(self, request, *args, **kwargs):
        role = Role.objects.get(pk=self.kwargs.get("role_id"))
        menu = Menu.objects.get(pk=self.kwargs.get("menu_id"))
        try:
            role_menu_privilege = RoleMenuPrivilege.objects.get(
                role=role, menu=menu, is_active=True
            )
        except Exception:
            raise serializers.ValidationError(
                {"message": "Role with this menu does not exist."}
            )
        custom_response = dict()
        # privilege = dict()
        privilege = list()
        for i in role_menu_privilege.privilege.all():
            # privilege.update({
            # i.code: i.is_active
            # })
            privilege.append(i.id)
        custom_response.update(
            {
                "menu_id": role_menu_privilege.menu.id,
                "menu_code": role_menu_privilege.menu.code,
                "menu_name": role_menu_privilege.menu.name,
                "privilege": privilege,
            }
        )
        return Response(custom_response)

    def delete(self, request, *args, **kwargs):
        role = Role.objects.get(pk=self.kwargs.get("role_id"))
        menu = Menu.objects.get(pk=self.kwargs.get("menu_id"))
        try:
            role_menu_privilege = RoleMenuPrivilege.objects.get(
                role=role, menu=menu, is_active=True
            )
        except Exception:
            raise serializers.ValidationError(
                {"message": "Role with this menu does not exist."}
            )
        role_menu_privilege.is_deleted = True
        role_menu_privilege.save()
        # create_log
        display_message = f" of Branch {(request.user.internal_user.branch)} deleted Menu {role_menu_privilege.menu.name} for Role {role_menu_privilege.role.name}."
        data = {
            "object_id": role_menu_privilege.id,
            "content_type": ContentType.objects.get(model="rolemenuprivilege"),
            "action_type": "delete",
            "display_message": display_message,
        }
        create_internal_user_activity_log(request, data)
        return Response({"message": "Menu privileges deleted successfylly."})


class AssignRoleMenuPrivilege(APIView):
    """
    Create Roles and its respective Privileges for Active Menu
    """

    def post(self, request, *args, **kwargs):
        serializer = RoleMenuPrivilegeSerializer(data=request.data)
        custom_response = dict()
        # privileges = dict()
        privileges = list()
        if serializer.is_valid(raise_exception=True):
            privilege = serializer.validated_data.get("privilege")
            instance, _ = RoleMenuPrivilege.objects.update_or_create(
                role=serializer.validated_data.get("role"),
                menu=serializer.validated_data.get("menu"),
                defaults={
                    "created_by": self.request.user,
                    "updated_by": self.request.user,
                },
            )
            instance.privilege.clear()
            if privilege:
                for i in privilege:
                    instance.privilege.add(i)
                for j in instance.privilege.all():
                    # privileges.update({
                    #     j.code: j.is_active
                    # })
                    privileges.append(j.id)
                priv_names = Privilege.objects.filter(id__in=privileges).values_list(
                    "name", flat=True
                )
                # create_log
                display_message = f" of Branch {(request.user.internal_user.branch)} added permission to {(', '.join(priv_names))} in menu {instance.menu.name} for Role {instance.role.name}."
                data = {
                    "object_id": instance.id,
                    "content_type": ContentType.objects.get(model="rolemenuprivilege"),
                    "action_type": "create",
                    "display_message": display_message,
                }
                create_internal_user_activity_log(request, data)
            custom_response.update(serializer.data)
            custom_response.update(
                {
                    "role": instance.role.name,
                    "menu": instance.menu.name,
                    "privilege": privileges,
                }
            )

        return Response(custom_response)


class AssignUsersToRole(APIView):
    """
    Assign and Remove Users from Role
    """

    def post(self, request, *args, **kwargs):
        role = get_object_or_404(Role, pk=self.kwargs.get("pk"))
        serializer = AssignUsersToRoleSerializer(role, data=request.data)
        if serializer.is_valid(raise_exception=True):
            if RoleMenuPrivilege.objects.filter(
                role__users__in=serializer.validated_data.get("users")
            ).exists():
                raise serializers.ValidationError(
                    {"message": "User has already been assigned to a role."}
                )
            role.users.add(
                *InternalUser.objects.filter(
                    pk__in=serializer.validated_data.get("users")
                )
            )
            # create_log
            user_names = InternalUser.objects.filter(
                pk__in=serializer.validated_data.get("users")
            )
            names = [i.get_full_name for i in user_names]
            display_message = f" of Branch {(request.user.internal_user.branch)} assigned {(', ').join(names)} to Role {role.name}."
            data = {
                "object_id": role.id,
                "content_type": ContentType.objects.get(model="role"),
                "action_type": "create",
                "display_message": display_message,
            }
            create_internal_user_activity_log(request, data)
        return Response({"message": "Users added to the role successfully."})

    def delete(self, request, *args, **kwargs):
        role = get_object_or_404(Role, pk=self.kwargs.get("pk"))
        serializer = AssignUsersToRoleSerializer(role, data=request.data)
        if serializer.is_valid(raise_exception=True):
            role.users.remove(
                *InternalUser.objects.filter(
                    pk__in=serializer.validated_data.get("users")
                )
            )
            # create_log
            user_names = InternalUser.objects.filter(
                pk__in=serializer.validated_data.get("users")
            )
            names = [i.get_full_name for i in user_names]
            display_message = f" of Branch {(request.user.internal_user.branch)} removed {(', ').join(names)} from Role {role.name}."
            data = {
                "object_id": role.id,
                "content_type": ContentType.objects.get(model="role"),
                "action_type": "delete",
                "display_message": display_message,
            }
            create_internal_user_activity_log(request, data)
        return Response({"message": "Users removed from the role successfully."})


class ForgotPassword(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            user = AuthUser.objects.get(
                email=request.data.get("email"), is_active=True, is_email_verified=True
            )
            key = generateKey()
            user.otp = key["OTP"]
            user.activation_key = key["totp"]
            user.save()
            msg = "Reset your account using the provided OTP."
            send_otp_email(request, user, key, msg)
            starttime = datetime.datetime.now()
            custom_response = {}
            custom_response["data"] = {
                "otp_starttime": starttime,
                "otp_expirytime": starttime + datetime.timedelta(seconds=300),
                "otp_length": len(str(user.otp)),
                "otp": user.otp,
                "email": user.email,
            }
            log_data = {
                "user": user,
                "otp_send_time": datetime.datetime.now(),
                "created_by": user,
            }
            OTPEnteredDetail.objects.create(**log_data)

            custom_response["message"] = "Please check your email for OTP."
            return Response(custom_response, status=status.HTTP_200_OK)
        except AuthUser.DoesNotExist:
            return Response(
                {"message": "Email is not associated with any user."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ConfirmResetPassword(PasswordResetConfirmView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "Password has been successfully reset."},
            status=status.HTTP_200_OK,
        )


class BankDetailInIndividualUserUpdateView(RetrieveUpdateAPIView):
    serializer_class = BankDetailInIndividualUserSerializer
    queryset = IndividualUser.objects.all()

    def perform_update(self, serializer):
        return serializer.save()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        user = self.request.user.individual_profile
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        banking_details = self.perform_update(serializer)
        resp_serializer = IndividualBankDetailListSerializer(banking_details)

        return Response(resp_serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.request.user.individual_profile
        serializer = IndividualBankDetailListSerializer(instance)
        return Response(serializer.data)


class BankDetailInInstitutionUserUpdateView(RetrieveUpdateAPIView):
    serializer_class = BankDetailInInstitutionUserSerializer
    queryset = InstitutionUser.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.request.user.institution_profile
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_response = self.perform_update(serializer)
        resp_serializer = InstitutionUserDetailListSerializer(updated_response)
        return Response(resp_serializer.data)

    def perform_update(self, serializer):
        return serializer.save(updated_by=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.request.user.institution_profile
        serializer = InstitutionUserDetailListSerializer(instance)

        return Response(serializer.data)


class GetUserMenuPrivilegeView(APIView):
    """
    Get User and its respective Privileges for Active Menu
    """

    def get(self, request, *args, **kwargs):
        user = InternalUser.objects.get(pk=self.kwargs.get("pk"))
        user_menu_privilege = UserMenuPrivilege.objects.filter(
            user=user, is_active=True
        ).order_by("menu__order_id")
        dict_items = dict()
        menus = list()
        for user_menu in user_menu_privilege:
            menus.append(
                {
                    "menu_id": user_menu.menu.id,
                    "menu_code": user_menu.menu.code,
                    "menu_name": user_menu.menu.name,
                }
            )

        dict_items.update(
            {"menu": menus, "user": InternalUserSerializerList(user, many=False).data}
        )
        return Response(dict_items)


class GetActiveUserMenuPrivilegeView(APIView):
    def get(self, request, *args, **kwargs):
        user = InternalUser.objects.get(pk=self.kwargs.get("user_id"))
        menu = Menu.objects.get(pk=self.kwargs.get("menu_id"))
        try:
            user_menu_privilege = UserMenuPrivilege.objects.get(
                user=user, menu=menu, is_active=True
            )
        except Exception:
            raise serializers.ValidationError(
                {"message": "Menu privilege with this id does not exist."}
            )
        custom_response = dict()
        privilege = list()
        for i in user_menu_privilege.privilege.all():
            privilege.append(i.id)
        custom_response.update(
            {
                "menu_id": user_menu_privilege.menu.id,
                "menu_code": user_menu_privilege.menu.code,
                "menu_name": user_menu_privilege.menu.name,
                "privilege": privilege,
            }
        )
        return Response(custom_response)

    def delete(self, request, *args, **kwargs):
        user = InternalUser.objects.get(pk=self.kwargs.get("user_id"))
        menu = Menu.objects.get(pk=self.kwargs.get("menu_id"))
        try:
            user_menu_privilege = UserMenuPrivilege.objects.get(
                user=user, menu=menu, is_active=True
            )
        except Exception:
            raise serializers.ValidationError(
                {"message": "Role with this menu does not exist."}
            )
        user_menu_privilege.is_deleted = True
        user_menu_privilege.save()
        return Response({"message": "Menu privileges deleted successfylly."})


class AssignUserMenuPrivilege(APIView):
    """
    Create User and its respective Privileges for Active Menu
    """

    def post(self, request, *args, **kwargs):
        serializer = UserMenuPrivilegeSerializer(data=request.data)
        custom_response = dict()
        privileges = list()
        if serializer.is_valid(raise_exception=True):
            privilege = serializer.validated_data.get("privilege")
            instance, _ = UserMenuPrivilege.objects.update_or_create(
                user=serializer.validated_data.get("user"),
                menu=serializer.validated_data.get("menu"),
                defaults={
                    "created_by": self.request.user,
                    "updated_by": self.request.user,
                },
            )

            # remove user from roles as user is assigned with specific privilege
            # roles = Role.objects.filter(
            #     users=serializer.validated_data.get('user'))
            # for i in roles:
            #     i.users.remove(serializer.validated_data.get('user'))

            instance.privilege.clear()
            if privilege:
                for i in privilege:
                    instance.privilege.add(i)
                for j in instance.privilege.all():
                    privileges.append(j.id)
            custom_response.update(serializer.data)
            custom_response.update(
                {
                    "user": instance.user.id,
                    "menu": instance.menu.name,
                    "privilege": privileges,
                    "message": "Menu privileges added successfully.",
                }
            )
        # create_log
        display_message = f" of Branch {(request.user.internal_user.branch)} edited permission for {instance.user}."
        data = {
            "object_id": instance.id,
            "content_type": ContentType.objects.get(model="usermenuprivilege"),
            "action_type": "create",
            "display_message": display_message,
        }
        create_internal_user_activity_log(request, data)
        return Response(custom_response)


class AllLoanList(ListAPIView):
    permission_classes = [
        InternalUserOnly,
    ]

    def list(self, request):
        filter_status = request.query_params.get("status", "1")
        loan_type = request.query_params.get("loan_type", "individual")

        if request.user.user_type == "1":
            internaluser = InternalUser.objects.get(user=request.user)
        else:
            return Response(
                {"message": "The user must be an internal user"},
                status.HTTP_400_BAD_REQUEST,
            )

        if loan_type == "institution":
            institutional_loans = InstitutionalForm.objects.filter(
                status=filter_status, applied_branch=internaluser.branch
            )
            page = self.paginate_queryset(institutional_loans)
            serializer = InstitutionalFormListSerializer(page, many=True)
        else:
            individual_loans = IndividualForm.objects.filter(
                status=filter_status, applied_branch=internaluser.branch
            )
            page = self.paginate_queryset(individual_loans)
            serializer = IndividualFormListSerializer(page, many=True)

        if page is not None:
            return self.get_paginated_response(serializer.data)

        return Response(serializer.data)


class UserRoleConfigurationMenuList(ListAPIView):
    queryset = Menu.objects.filter(is_active=True).order_by("order_id")
    serializer_class = MenuSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset_1 = Menu.objects.filter(
            is_active=True, user_type="1", parent__isnull=False, is_tab=False
        ).order_by("order_id")
        queryset_2 = Menu.objects.filter(
            code__in=["internal_dashboard", "base_config", "psychometric_test"]
        )
        queryset = queryset_1 | queryset_2
        screen = self.request.GET.get("screen")
        id = self.request.GET.get("id")
        active_menus = list()
        if screen and id:
            if screen == "roles":
                roles = RoleMenuPrivilege.objects.filter(role=id).distinct()
                for i in roles:
                    active_menus.append(i.menu.id)
                return queryset.exclude(id__in=active_menus)
            elif screen == "users":
                users = UserMenuPrivilege.objects.filter(user=id).distinct()
                for i in users:
                    active_menus.append(i.menu.id)
                return queryset.exclude(id__in=active_menus)
        return queryset


class GenerateCustomerListReportView(APIView):
    """
    Generate Pdf report of Customer List
    """

    template_name = "reports/customer-list.html"

    def post(self, request, *args, **kwargs):
        pdf_filename = (
            "customer-list-" + datetime.date.today().strftime("%Y-%m-%d") + ".pdf"
        )
        context = {
            "individual": IndividualUser.objects.all(),
            "institution": InstitutionUser.objects.all(),
        }

        customer_list_pdf = export_to_pdf(
            pdf_filename, self.template_name, context, request
        )
        return customer_list_pdf


class DashboardView(APIView):
    def get(self, request, *args, **kwargs):

        # get individual, institutional form according to requested user branch
        (
            individualform,
            institutionalform,
            agricultural_loan,
            non_agricultural_loan,
        ) = get_form_according_to_user(request)

        total_application = agricultural_loan + non_agricultural_loan

        active_users_individual_form = set(
            individualform.filter(user__user__is_active=True).values_list("user_id")
        )
        active_users_institutional_form = set(
            institutionalform.filter(user__user__is_active=True).values_list("user_id")
        )
        active_users = len(active_users_individual_form) + len(
            active_users_institutional_form
        )
        data = {
            "agricultural_loan": agricultural_loan,
            "non_agricultural_loan": non_agricultural_loan,
            "total_application": total_application,
            "active_users": active_users,
        }
        return Response(data)


class DashboardStatusWiseView(APIView):
    def get(self, request, *args, **kwargs):
        # status wise

        (
            individualform,
            institutionalform,
            agricultural_loan,
            non_agricultural_loan,
        ) = get_form_according_to_user(request)

        statuses = [
            ("1", "in_progress"),
            ("2", "pending"),
            ("4", "rejected"),
            ("5", "verified"),
            ("6", "re_applied"),
            ("7", "final_submission"),
            ("3", "approved"),
            ("8", "final_rejection"),
        ]
        graph = get_status_wise_forms(
            request,
            statuses,
            individualform,
            institutionalform,
            agricultural_loan,
            non_agricultural_loan,
        )

        data = {
            "graph": graph,
        }
        return Response(data)


class InternalUserPasswordResetView(APIView):
    def post(self, request, *args, **kwargs):
        internal_user = InternalUser.admin_objects.get(pk=self.kwargs.get("pk"))
        user = User.objects.get(internal_user=internal_user)
        auto_password = User.objects.make_random_password()
        user.set_password(auto_password)
        user.need_password_change = True
        user.save()
        subject = "Password Reset - Agriculture Development Bank Ltd."
        message = render_to_string(
            "internal-user-credentials.html",
            {
                "logo": self.request.build_absolute_uri("/static/images/logo.png"),
                "email": user.email,
                "username": user.username,
                "password": auto_password,
            },
        )
        internal_user_credential_email.delay(subject, message, user.email)
        return Response({"message": "Password Reset Successfully."})


class InternalUserProfileBranchAndProvinceList(ListAPIView):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    pagination_class = None

    def get_serializer_class(self):
        serializer = super().get_serializer_class()
        _data = self.request.GET.get("data", None)
        if not _data or _data not in ["province", "branch"]:
            raise serializers.ValidationError(
                {"message": "Data options are branch and province only."}
            )
        else:
            if _data == "province":
                serializer = ProvinceSerializer
            else:
                serializer = BranchSerializer
        return serializer

    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.request
        _data = self.request.GET.get("data", None)
        province_id = self.request.query_params.get("province_id", None)
        internal_user = InternalUser.objects.get(user=self.request.user)

        if _data not in ["province", "branch"]:
            raise serializers.ValidationError(
                {"message": "Data options are branch and province only."}
            )
        else:
            if _data == "province":
                if request.user.is_superuser or (
                    request.user.user_type == "1"
                    and internal_user.branch.is_head_office
                ):
                    queryset = Province.objects.filter(show_to_public=False)
                elif request.user.user_type == "1":
                    queryset = Province.objects.filter(
                        province_branch=internal_user.branch, show_to_public=False
                    )
                else:
                    raise serializers.ValidationError({"message": "Unauthorized"})
            else:
                if request.user.is_superuser or (
                    request.user.user_type == "1"
                    and internal_user.branch.is_head_office
                ):
                    try:
                        province = Province.objects.get(
                            id=province_id, show_to_public=False
                        )
                        queryset = (
                            Branch.objects.filter(province=province)
                            .exclude(is_head_office=True)
                            .exclude(is_province_office=True)
                        )
                    except:
                        queryset = Branch.objects.all()
                elif request.user.user_type == "1":
                    if internal_user.branch.is_province_office:
                        queryset = Branch.objects.filter(
                            province=internal_user.branch.province
                        )
                    else:
                        queryset = Branch.objects.filter(id=internal_user.branch.id)
                else:
                    raise serializers.ValidationError({"message": "Unauthorized"})
        return queryset


class AssignMultipleMenusRoleAndUserView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AssignMultipleMenusRoleAndUserSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            screen_id = serializer.validated_data.get("id")
            type = serializer.validated_data.get("type")
            menus = serializer.validated_data.get("menus")
            if type == "users":
                user_privileges = [
                    UserMenuPrivilege(
                        user=InternalUser.objects.get(id=screen_id),
                        menu=Menu.objects.get(id=menu),
                    )
                    for menu in menus
                    if menu
                ]
                UserMenuPrivilege.objects.bulk_create(user_privileges)
            elif type == "roles":
                role_privileges = [
                    RoleMenuPrivilege(
                        role=Role.objects.get(id=screen_id),
                        menu=Menu.objects.get(id=menu),
                    )
                    for menu in menus
                    if menu
                ]
                RoleMenuPrivilege.objects.bulk_create(role_privileges)
            message = f"{(', '.join(Menu.objects.filter(id__in=menus).values_list('name', flat=True)))} added successfully to {InternalUser.objects.get(id=screen_id).get_full_name if type == 'users' else Role.objects.get(id=screen_id).name}"
        return Response(message, status=status.HTTP_201_CREATED)


class ChangeMobileNumberVerifyOTP(APIView):
    """
    Verify OTP entered by the user and change the mobile number
    """

    permission_classes = [
        AllowAny,
    ]

    def post(self, request, *args, **kwargs):
        otp = request.data.get("otp")
        try:
            user = AuthUser.objects.get(otp=int(otp))
            verify = verify_otp(user.activation_key, otp)
            if verify:
                user.mobile_number = user.temporary_number
                user.otp = None
                user.activation_key = None
                user.temporary_number = None
                user.save()
                return Response({"message": "Mobile number changed successfully."})
            else:
                return Response(
                    {"message": "Given otp is expired!!"},
                    status=status.HTTP_408_REQUEST_TIMEOUT,
                )
        except Exception:
            return Response(
                {"message": "Invalid otp OR No any inactive user found for given otp"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangeMobileNumberForUsersView(APIView):
    """
    Send OTP to the new mobile number entered by the user
    """

    # permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs):
        user = self.request.user
        serializer = ChangeMobileNumberForUsersSerializer(
            data=request.data, context={"request": request}
        )
        custom_response = dict()
        if serializer.is_valid(raise_exception=True):
            new_number = serializer.validated_data.get("new_number")
            key = generateKey()
            user.otp = key["OTP"]
            user.activation_key = key["totp"]
            user.temporary_number = new_number
            otp_response = change_mobile_number_send_otp.delay(new_number, key).get()
            # otp_response = change_mobile_number_send_otp(new_number, key)
            fail_count = 0

            # send otp until status is success and fail_count is less than 5
            while otp_response != 200 and fail_count < 5:
                otp_response = change_mobile_number_send_otp.delay(
                    new_number, key
                ).get()
                fail_count += 1

            #  update user details only if otp is successfully sent
            if otp_response == 200:
                user.save()

                # generate new nonce and add count for sms service
                sms_service = SmsService.objects.filter(is_active=True).first()
                sms_service.nonce = secrets.token_urlsafe()
                sms_service.count += 1
                sms_service.save()

                custom_response.update(serializer.data)
                custom_response["otp_starttime"] = datetime.datetime.now()
                custom_response["otp_expirytime"] = custom_response.get(
                    "otp_starttime"
                ) + datetime.timedelta(seconds=300)
                custom_response["otp_length"] = len(str(user.otp))
                custom_response["otp"] = user.otp
            else:
                custom_response.update(
                    {"message": "Invalid time out!! Please try again."}
                )
        return Response(custom_response)


class MobileNumberChangeResendOtp(APIView):
    def post(self, request, *args, **kwargs):
        mobile_number = request.data.get("mobile_number")
        user = self.request.user
        if mobile_number != user.temporary_number:
            raise serializers.ValidationError(
                {"message": "Mobile number does not match"}
            )
        key = generateKey()
        user.otp = key["OTP"]
        user.activation_key = key["totp"]
        user.save()
        custom_response = dict()
        otp_response = change_mobile_number_send_otp.delay(mobile_number, key).get()
        fail_count = 0

        # send otp until status is success and fail_count is less than 5
        while otp_response == "error" and fail_count < 5:
            otp_response = change_mobile_number_send_otp.delay(mobile_number, key).get()
            fail_count += 1

        #  update user details only if otp is successfully sent
        if otp_response == "success":
            user.save()
            custom_response["otp_starttime"] = datetime.datetime.now()
            custom_response["otp_expirytime"] = custom_response.get(
                "otp_starttime"
            ) + datetime.timedelta(seconds=300)
            custom_response["otp_length"] = len(str(user.otp))
            custom_response["otp"] = user.otp
        else:
            custom_response.update({"message": "Invalid time out!! Please try again."})
        return Response(custom_response, status=status.HTTP_200_OK)
