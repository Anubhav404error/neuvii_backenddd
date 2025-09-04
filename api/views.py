from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.db import transaction

from users.models import User, Role
from clinic.models import Clinic
from therapy.models import (
    TherapistProfile, ParentProfile, Child, Assignment,
    SpeechArea, LongTermGoal, ShortTermGoal, Task
)
from .serializers import (
    LoginSerializer, UserSerializer, RoleSerializer, ClinicSerializer,
    TherapistProfileSerializer, ParentProfileSerializer, ChildSerializer,
    AssignmentSerializer, SpeechAreaSerializer, LongTermGoalSerializer,
    ShortTermGoalSerializer, TaskSerializer, TaskAssignmentSerializer,
    PasswordChangeSerializer
)


# Authentication Views
class LoginAPIView(APIView):
    """
    User login endpoint that returns JWT tokens
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Check if password reset is required
            if user.password_reset_required:
                return Response({
                    'error': 'Password reset required',
                    'password_reset_required': True,
                    'message': 'You must change your password before accessing the system.'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    User logout endpoint
    """
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Successfully logged out'})
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordAPIView(APIView):
    """
    Change user password endpoint
    """
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.password_reset_required = False
            user.save()
            
            return Response({'message': 'Password changed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# User Management Views
class UserListAPIView(generics.ListCreateAPIView):
    """
    List all users or create a new user
    """
    serializer_class = UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        
        # Role-based filtering
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=user)
                # Show therapists and parents from their clinic
                therapist_emails = TherapistProfile.objects.filter(clinic=clinic).values_list('email', flat=True)
                parent_emails = ParentProfile.objects.filter(clinic=clinic).values_list('parent_email', flat=True)
                clinic_user_emails = list(therapist_emails) + list(parent_emails)
                clinic_user_emails = [email for email in clinic_user_emails if email]
                return User.objects.filter(email__in=clinic_user_emails)
            except Clinic.DoesNotExist:
                return User.objects.none()
        
        return User.objects.none()


class UserDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a user
    """
    serializer_class = UserSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        
        # Users can only access their own profile
        return User.objects.filter(id=user.id)


# Role Views
class RoleListAPIView(generics.ListAPIView):
    """
    List all roles
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


# Clinic Views
class ClinicListAPIView(generics.ListCreateAPIView):
    """
    List all clinics or create a new clinic
    """
    serializer_class = ClinicSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Clinic.objects.all()
        
        # Clinic admin sees only their clinic
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "clinic admin":
            return Clinic.objects.filter(clinic_admin=user)
        
        return Clinic.objects.none()


class ClinicDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a clinic
    """
    serializer_class = ClinicSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Clinic.objects.all()
        
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "clinic admin":
            return Clinic.objects.filter(clinic_admin=user)
        
        return Clinic.objects.none()


# Therapist Views
class TherapistProfileListAPIView(generics.ListCreateAPIView):
    """
    List all therapists or create a new therapist
    """
    serializer_class = TherapistProfileSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return TherapistProfile.objects.all()
        
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "therapist":
            return TherapistProfile.objects.filter(email=user.email)
        elif role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=user)
                return TherapistProfile.objects.filter(clinic=clinic)
            except Clinic.DoesNotExist:
                return TherapistProfile.objects.none()
        
        return TherapistProfile.objects.none()


class TherapistProfileDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a therapist profile
    """
    serializer_class = TherapistProfileSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return TherapistProfile.objects.all()
        
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "therapist":
            return TherapistProfile.objects.filter(email=user.email)
        elif role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=user)
                return TherapistProfile.objects.filter(clinic=clinic)
            except Clinic.DoesNotExist:
                return TherapistProfile.objects.none()
        
        return TherapistProfile.objects.none()


# Parent/Client Views
class ParentProfileListAPIView(generics.ListCreateAPIView):
    """
    List all clients or create a new client
    """
    serializer_class = ParentProfileSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ParentProfile.objects.all()
        
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "parent":
            return ParentProfile.objects.filter(parent_email=user.email)
        elif role == "therapist":
            return ParentProfile.objects.filter(assigned_therapist__email=user.email)
        elif role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=user)
                return ParentProfile.objects.filter(clinic=clinic)
            except Clinic.DoesNotExist:
                return ParentProfile.objects.none()
        
        return ParentProfile.objects.none()


class ParentProfileDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a client profile
    """
    serializer_class = ParentProfileSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return ParentProfile.objects.all()
        
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "parent":
            return ParentProfile.objects.filter(parent_email=user.email)
        elif role == "therapist":
            return ParentProfile.objects.filter(assigned_therapist__email=user.email)
        elif role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=user)
                return ParentProfile.objects.filter(clinic=clinic)
            except Clinic.DoesNotExist:
                return ParentProfile.objects.none()
        
        return ParentProfile.objects.none()


# Child Views
class ChildListAPIView(generics.ListCreateAPIView):
    """
    List all children or create a new child
    """
    serializer_class = ChildSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Child.objects.all()
        
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "parent":
            return Child.objects.filter(parent__parent_email=user.email)
        elif role == "therapist":
            return Child.objects.filter(assigned_therapist__email=user.email)
        elif role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=user)
                return Child.objects.filter(clinic=clinic)
            except Clinic.DoesNotExist:
                return Child.objects.none()
        
        return Child.objects.none()


class ChildDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a child
    """
    serializer_class = ChildSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Child.objects.all()
        
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "parent":
            return Child.objects.filter(parent__parent_email=user.email)
        elif role == "therapist":
            return Child.objects.filter(assigned_therapist__email=user.email)
        elif role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=user)
                return Child.objects.filter(clinic=clinic)
            except Clinic.DoesNotExist:
                return Child.objects.none()
        
        return Child.objects.none()


# Speech Therapy Structure Views
class SpeechAreaListAPIView(generics.ListCreateAPIView):
    """
    List all speech areas or create a new speech area
    """
    queryset = SpeechArea.objects.filter(is_active=True)
    serializer_class = SpeechAreaSerializer


class SpeechAreaDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a speech area
    """
    queryset = SpeechArea.objects.all()
    serializer_class = SpeechAreaSerializer


class LongTermGoalListAPIView(generics.ListCreateAPIView):
    """
    List long-term goals or create a new long-term goal
    """
    serializer_class = LongTermGoalSerializer
    
    def get_queryset(self):
        queryset = LongTermGoal.objects.filter(is_active=True)
        speech_area_id = self.request.query_params.get('speech_area_id')
        if speech_area_id:
            queryset = queryset.filter(speech_area_id=speech_area_id)
        return queryset


class LongTermGoalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a long-term goal
    """
    queryset = LongTermGoal.objects.all()
    serializer_class = LongTermGoalSerializer


class ShortTermGoalListAPIView(generics.ListCreateAPIView):
    """
    List short-term goals or create a new short-term goal
    """
    serializer_class = ShortTermGoalSerializer
    
    def get_queryset(self):
        queryset = ShortTermGoal.objects.filter(is_active=True)
        long_term_goal_id = self.request.query_params.get('long_term_goal_id')
        if long_term_goal_id:
            queryset = queryset.filter(long_term_goal_id=long_term_goal_id)
        return queryset


class ShortTermGoalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a short-term goal
    """
    queryset = ShortTermGoal.objects.all()
    serializer_class = ShortTermGoalSerializer


class TaskListAPIView(generics.ListCreateAPIView):
    """
    List tasks or create a new task
    """
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        queryset = Task.objects.filter(is_active=True)
        short_term_goal_id = self.request.query_params.get('short_term_goal_id')
        difficulty = self.request.query_params.get('difficulty')
        
        if short_term_goal_id:
            queryset = queryset.filter(short_term_goal_id=short_term_goal_id)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        return queryset


class TaskDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a task
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer


# Assignment Views
class AssignmentListAPIView(generics.ListCreateAPIView):
    """
    List assignments or create a new assignment
    """
    serializer_class = AssignmentSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Assignment.objects.all()
        
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "parent":
            return Assignment.objects.filter(child__parent__parent_email=user.email)
        elif role == "therapist":
            return Assignment.objects.filter(therapist__email=user.email)
        
        return Assignment.objects.none()


class AssignmentDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an assignment
    """
    serializer_class = AssignmentSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Assignment.objects.all()
        
        role = getattr(getattr(user, "role", None), "name", "").lower()
        if role == "parent":
            return Assignment.objects.filter(child__parent__parent_email=user.email)
        elif role == "therapist":
            return Assignment.objects.filter(therapist__email=user.email)
        
        return Assignment.objects.none()


# Task Assignment API
class AssignTasksAPIView(APIView):
    """
    Assign multiple tasks to a client's child
    """
    def post(self, request):
        serializer = TaskAssignmentSerializer(data=request.data)
        if serializer.is_valid():
            parent_id = serializer.validated_data['parent_id']
            selected_tasks = serializer.validated_data['selected_tasks']
            
            # Get parent and verify access
            parent = get_object_or_404(ParentProfile, id=parent_id)
            
            # Verify therapist has access to this parent
            if not request.user.is_superuser:
                role = getattr(getattr(request.user, "role", None), "name", "").lower()
                if role == "therapist":
                    therapist = TherapistProfile.objects.filter(email=request.user.email).first()
                    if not therapist or parent.assigned_therapist != therapist:
                        return Response(
                            {'error': 'You do not have permission to assign tasks to this client'},
                            status=status.HTTP_403_FORBIDDEN
                        )
            
            # Get or create child record
            child = parent.children.first()
            if not child:
                child = Child.objects.create(
                    name=f"{parent.first_name} {parent.last_name}",
                    age=parent.age or 5,
                    gender='other',
                    clinic=parent.clinic,
                    parent=parent,
                    assigned_therapist=parent.assigned_therapist
                )
            
            # Get therapist
            therapist = TherapistProfile.objects.filter(email=request.user.email).first()
            if not therapist:
                return Response(
                    {'error': 'Therapist profile not found'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create assignments
            assignments_created = 0
            with transaction.atomic():
                for task_id in selected_tasks:
                    task = get_object_or_404(Task, id=task_id)
                    
                    # Check if assignment already exists
                    if not Assignment.objects.filter(child=child, task=task, therapist=therapist).exists():
                        Assignment.objects.create(
                            child=child,
                            task=task,
                            therapist=therapist
                        )
                        assignments_created += 1
            
            return Response({
                'success': True,
                'message': f'{assignments_created} tasks assigned successfully to {child.name}',
                'child_name': child.name,
                'assignments_created': assignments_created
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Dashboard/Statistics Views
class DashboardStatsAPIView(APIView):
    """
    Get dashboard statistics based on user role
    """
    def get(self, request):
        user = request.user
        role = getattr(getattr(user, "role", None), "name", "").lower()
        
        stats = {}
        
        if user.is_superuser:
            stats = {
                'total_clinics': Clinic.objects.count(),
                'total_therapists': TherapistProfile.objects.count(),
                'total_clients': ParentProfile.objects.count(),
                'total_children': Child.objects.count(),
                'total_assignments': Assignment.objects.count(),
                'active_assignments': Assignment.objects.filter(completed=False).count(),
            }
        elif role == "clinic admin":
            from clinic.models import Clinic
            try:
                clinic = Clinic.objects.get(clinic_admin=user)
                stats = {
                    'clinic_name': clinic.name,
                    'therapists_count': TherapistProfile.objects.filter(clinic=clinic).count(),
                    'clients_count': ParentProfile.objects.filter(clinic=clinic).count(),
                    'children_count': Child.objects.filter(clinic=clinic).count(),
                }
            except Clinic.DoesNotExist:
                stats = {'error': 'Clinic not found'}
        elif role == "therapist":
            therapist = TherapistProfile.objects.filter(email=user.email).first()
            if therapist:
                stats = {
                    'therapist_name': f"{therapist.first_name} {therapist.last_name}",
                    'assigned_clients': ParentProfile.objects.filter(assigned_therapist=therapist).count(),
                    'total_assignments': Assignment.objects.filter(therapist=therapist).count(),
                    'pending_assignments': Assignment.objects.filter(therapist=therapist, completed=False).count(),
                    'completed_assignments': Assignment.objects.filter(therapist=therapist, completed=True).count(),
                }
        elif role == "parent":
            parent = ParentProfile.objects.filter(parent_email=user.email).first()
            if parent:
                children = parent.children.all()
                total_assignments = Assignment.objects.filter(child__in=children)
                stats = {
                    'parent_name': f"{parent.first_name} {parent.last_name}",
                    'children_count': children.count(),
                    'total_assignments': total_assignments.count(),
                    'pending_assignments': total_assignments.filter(completed=False).count(),
                    'completed_assignments': total_assignments.filter(completed=True).count(),
                }
        
        return Response(stats)


# Utility Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile(request):
    """
    Get current user's profile information
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def therapist_clients(request):
    """
    Get clients assigned to the current therapist
    """
    role = getattr(getattr(request.user, "role", None), "name", "").lower()
    if role != "therapist":
        return Response({'error': 'Only therapists can access this endpoint'}, status=status.HTTP_403_FORBIDDEN)
    
    therapist = TherapistProfile.objects.filter(email=request.user.email).first()
    if not therapist:
        return Response({'error': 'Therapist profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    clients = ParentProfile.objects.filter(assigned_therapist=therapist)
    serializer = ParentProfileSerializer(clients, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def parent_children(request):
    """
    Get children for the current parent
    """
    role = getattr(getattr(request.user, "role", None), "name", "").lower()
    if role != "parent":
        return Response({'error': 'Only parents can access this endpoint'}, status=status.HTTP_403_FORBIDDEN)
    
    parent = ParentProfile.objects.filter(parent_email=request.user.email).first()
    if not parent:
        return Response({'error': 'Parent profile not found'}, status=status.HTTP_404_NOT_FOUND)
    
    children = parent.children.all()
    serializer = ChildSerializer(children, many=True)
    return Response(serializer.data)