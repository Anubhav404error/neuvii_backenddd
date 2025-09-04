from django.contrib import admin
from django import forms
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.template.response import TemplateResponse

from neuvii_backend.admin_sites import neuvii_admin_site
from .models import TherapistProfile, ParentProfile, Child, Assignment, SpeechArea, LongTermGoal, ShortTermGoal, Task
from users.models import Role
from users.utils import create_user_with_role

User = get_user_model()

# ==========
# Utilities
# ==========
def _role_name(user):
    return getattr(getattr(user, "role", None), "name", "").lower()


# ===========================
# Speech Area Admin
# ===========================
@admin.register(SpeechArea, site=neuvii_admin_site)
class SpeechAreaAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'is_active']
    search_fields = ['name']
    list_filter = ['is_active']


# ===========================
# Long-Term Goal Admin
# ===========================
@admin.register(LongTermGoal, site=neuvii_admin_site)
class LongTermGoalAdmin(admin.ModelAdmin):
    list_display = ['id', 'speech_area', 'title', 'is_active']
    search_fields = ['title']
    list_filter = ['speech_area', 'is_active']


# ===========================
# Short-Term Goal Admin
# ===========================
@admin.register(ShortTermGoal, site=neuvii_admin_site)
class ShortTermGoalAdmin(admin.ModelAdmin):
    list_display = ['id', 'long_term_goal', 'title', 'is_active']
    search_fields = ['title']
    list_filter = ['long_term_goal__speech_area', 'is_active']


# ===========================
# Task Admin
# ===========================
@admin.register(Task, site=neuvii_admin_site)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id', 'short_term_goal', 'title', 'difficulty', 'is_active']
    search_fields = ['title']
    list_filter = ['difficulty', 'is_active', 'short_term_goal__long_term_goal__speech_area']


# ===========================
# Therapist Profile Admin
# ===========================
class TherapistProfileForm(forms.ModelForm):
    class Meta:
        model = TherapistProfile
        fields = "__all__"
        widgets = {"date_added": forms.DateInput(attrs={"type": "date"})}


@admin.register(TherapistProfile, site=neuvii_admin_site)
class TherapistProfileAdmin(admin.ModelAdmin):
    form = TherapistProfileForm
    list_display = ["id", "first_name", "last_name", "email", "phone_number", "is_active", "date_added"]
    search_fields = ["first_name", "last_name", "email", "phone_number"]
    list_filter = ["is_active", "date_added"]
    exclude = ["clinic"]
    readonly_fields = ["date_added"]

    # Scope visible rows
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        role = _role_name(request.user)
        if request.user.is_superuser:
            return qs
        if role == "therapist":
            return qs.filter(email=request.user.email)
        if role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=request.user)
                return qs.filter(clinic=clinic)
            except Clinic.DoesNotExist:
                return qs.none()
        return qs.none()

    # Restrict who can change/add/delete
    def has_add_permission(self, request):
        return _role_name(request.user) in ("clinic admin",) or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        role = _role_name(request.user)
        if request.user.is_superuser:
            return True
        if role == "therapist":
            # Therapist can edit ONLY their own profile
            return obj is None or (obj and obj.email == request.user.email)
        if role == "clinic admin":
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        role = _role_name(request.user)
        return role == "clinic admin" or request.user.is_superuser

    # Auto-attach clinic for clinic admin creating therapist
    def save_model(self, request, obj, form, change):
        role = _role_name(request.user)
        if not change and role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=request.user)
                obj.clinic = clinic
            except Clinic.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)

        # Note: User creation is now handled by signal in models.py


# ===========================
# Parent (Client) Admin
# ===========================
class ParentProfileForm(forms.ModelForm):
    class Meta:
        model = ParentProfile
        fields = [
            "first_name", "last_name", "parent_email", "phone_number",
            "age", "fscd_approval", "assigned_therapist"
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        # Limit therapist choices for clinic admin; superuser sees all
        if self.request:
            role = _role_name(self.request.user)
            if role == "clinic admin":
                from clinic.models import Clinic
                try:
                    clinic = Clinic.objects.get(clinic_admin=self.request.user)
                    self.fields["assigned_therapist"].queryset = TherapistProfile.objects.filter(clinic=clinic)
                except Clinic.DoesNotExist:
                    self.fields["assigned_therapist"].queryset = TherapistProfile.objects.none()
            elif self.request.user.is_superuser:
                self.fields["assigned_therapist"].queryset = TherapistProfile.objects.all()


@admin.register(ParentProfile, site=neuvii_admin_site)
class ParentProfileAdmin(admin.ModelAdmin):
    form = ParentProfileForm
    list_display = [
        "id", "first_name", "last_name", "parent_email", "phone_number",
        "age", "fscd_approval", "assigned_therapist", "clinic", "date_added", "is_active"
    ]
    search_fields = ["first_name", "last_name", "parent_email", "phone_number"]
    list_filter = ["clinic", "fscd_approval", "is_active"]
    readonly_fields = ["date_added"]

    def changelist_view(self, request, extra_context=None):
        """Add custom button to changelist view for therapists only"""
        extra_context = extra_context or {}
        
        # Only show assign task button for therapists (not clinic admin)
        role = getattr(getattr(request.user, "role", None), "name", "").lower()
        extra_context['show_assign_task_button'] = (role == "therapist")
        
        return super().changelist_view(request, extra_context=extra_context)

    # Provide request to form
    def get_form(self, request, obj=None, **kwargs):
        kwargs["form"] = self.form
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form

    # Scope rows by role
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        role = _role_name(request.user)
        if request.user.is_superuser:
            return qs
        if role == "parent":
            return qs.filter(parent_email=request.user.email)
        if role == "therapist":
            return qs.filter(assigned_therapist__email=request.user.email)
        if role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=request.user)
                return qs.filter(clinic=clinic)
            except Clinic.DoesNotExist:
                return qs.none()
        return qs.none()

    # Permissions:
    # Parent -> edit own profile only
    # Therapist -> view only
    # Clinic admin -> full (for their clinic)
    def has_add_permission(self, request):
        role = _role_name(request.user)
        return role in ("clinic admin",) or request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        role = _role_name(request.user)
        if request.user.is_superuser:
            return True
        if role == "parent":
            return obj is None or (obj and obj.parent_email == request.user.email)
        if role == "therapist":
            return False  # view-only
        if role == "clinic admin":
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        role = _role_name(request.user)
        return role == "clinic admin" or request.user.is_superuser

    # Auto-attach clinic on create by clinic admin; create linked user for parent
    def save_model(self, request, obj, form, change):
        role = _role_name(request.user)
        if not change and role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=request.user)
                obj.clinic = clinic
            except Clinic.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)

        # Note: User creation is now handled by signal in models.py


# ===========================
# Assignment Admin (Tasks)
# ===========================
@admin.register(Assignment, site=neuvii_admin_site)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ["id", "task", "child", "therapist", "assigned_date", "due_date", "completed"]
    search_fields = ["task__title", "child__name", "therapist__first_name", "therapist__last_name"]
    list_filter = ["completed", "due_date"]

    def changelist_view(self, request, extra_context=None):
        """Customize changelist view for therapists to show assign task button"""
        extra_context = extra_context or {}
        
        # Only show custom button for therapists
        role = getattr(getattr(request.user, "role", None), "name", "").lower()
        if role == "therapist":
            extra_context['show_assign_task_button'] = True
            # Get therapist's clients for the button
            therapist = TherapistProfile.objects.filter(email=request.user.email).first()
            if therapist:
                clients = ParentProfile.objects.filter(assigned_therapist=therapist)
                extra_context['therapist_clients'] = clients
        
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        """Hide the default Add Assignment button for therapists"""
        role = getattr(getattr(request.user, "role", None), "name", "").lower()
        if role == "therapist":
            return False  # Hide default add button for therapists
        return request.user.is_superuser

    # Scope visible rows by role
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        role = _role_name(request.user)
        if request.user.is_superuser:
            return qs
        if role == "parent":
            return qs.filter(child__parent__parent_email=request.user.email)
        if role == "therapist":
            # Tasks assigned by this therapist (their workload)
            return qs.filter(therapist__email=request.user.email)
        if role == "clinic admin":
            # Clinic admin CANNOT see assignments
            return qs.none()
        return qs.none()

    # Permissions:
    # - Therapist: full (add/change/delete/view) BUT only for their own assignments
    # - Parent: view only
    # - Clinic admin: no access (hidden by menu and permissions)
    def has_module_permission(self, request):
        role = _role_name(request.user)
        if request.user.is_superuser:
            return True
        if role in ("therapist", "parent"):
            return True
        return False

    def has_change_permission(self, request, obj=None):
        role = _role_name(request.user)
        if request.user.is_superuser:
            return True
        if role == "therapist":
            # Therapists can edit only assignments they own
            return obj is None or (obj and obj.therapist and obj.therapist.email == request.user.email)
        if role == "parent":
            return False
        return False

    def has_delete_permission(self, request, obj=None):
        role = _role_name(request.user)
        if request.user.is_superuser:
            return True
        if role == "therapist":
            return obj is None or (obj and obj.therapist and obj.therapist.email == request.user.email)
        return False
