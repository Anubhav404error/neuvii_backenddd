from rest_framework import permissions
from therapy.models import TherapistProfile, ParentProfile
from clinic.models import Clinic


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object.
        return obj.owner == request.user


class IsTherapistOrReadOnly(permissions.BasePermission):
    """
    Custom permission for therapist-specific actions
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        role = getattr(getattr(request.user, "role", None), "name", "").lower()
        return role == "therapist"


class IsClinicAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission for clinic admin actions
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        role = getattr(getattr(request.user, "role", None), "name", "").lower()
        return role == "clinic admin"


class IsParentOrReadOnly(permissions.BasePermission):
    """
    Custom permission for parent-specific actions
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        role = getattr(getattr(request.user, "role", None), "name", "").lower()
        return role == "parent"


class CanAccessClient(permissions.BasePermission):
    """
    Permission to check if user can access specific client data
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        role = getattr(getattr(request.user, "role", None), "name", "").lower()
        
        if role == "parent":
            # Parents can only access their own profile
            return obj.parent_email == request.user.email
        elif role == "therapist":
            # Therapists can access their assigned clients
            therapist = TherapistProfile.objects.filter(email=request.user.email).first()
            return therapist and obj.assigned_therapist == therapist
        elif role == "clinic admin":
            # Clinic admin can access clients from their clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=request.user)
                return obj.clinic == clinic
            except Clinic.DoesNotExist:
                return False
        
        return False


class CanAccessAssignment(permissions.BasePermission):
    """
    Permission to check if user can access specific assignment data
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        
        role = getattr(getattr(request.user, "role", None), "name", "").lower()
        
        if role == "parent":
            # Parents can access assignments for their children
            return obj.child.parent.parent_email == request.user.email
        elif role == "therapist":
            # Therapists can access assignments they created
            return obj.therapist.email == request.user.email
        
        return False