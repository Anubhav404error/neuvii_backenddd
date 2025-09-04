from rest_framework import serializers
from django.contrib.auth import authenticate
from users.models import User, Role
from clinic.models import Clinic
from therapy.models import (
    TherapistProfile, ParentProfile, Child, Assignment,
    SpeechArea, LongTermGoal, ShortTermGoal, Task
)


# Authentication Serializers
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password.')

        return attrs


class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'name']


# Clinic Serializers
class ClinicSerializer(serializers.ModelSerializer):
    clinic_admin_name = serializers.CharField(source='clinic_admin.get_full_name', read_only=True)

    class Meta:
        model = Clinic
        fields = [
            'id', 'name', 'address_line_1', 'address_line_2', 'city', 'country',
            'contact_person_name', 'role', 'email', 'clinic_admin', 'clinic_admin_name',
            'agreement_signed', 'license_status', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# Therapy Serializers
class TherapistProfileSerializer(serializers.ModelSerializer):
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)
    assigned_clients_count = serializers.SerializerMethodField()

    class Meta:
        model = TherapistProfile
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'clinic', 'clinic_name', 'is_active', 'date_added', 'assigned_clients_count'
        ]
        read_only_fields = ['id', 'date_added']

    def get_assigned_clients_count(self, obj):
        return obj.assigned_clients.count()


class ChildSerializer(serializers.ModelSerializer):
    parent_name = serializers.CharField(source='parent.get_full_name', read_only=True)
    therapist_name = serializers.CharField(source='assigned_therapist.get_full_name', read_only=True)
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)

    class Meta:
        model = Child
        fields = [
            'id', 'name', 'age', 'gender', 'parent', 'parent_name',
            'assigned_therapist', 'therapist_name', 'clinic', 'clinic_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ParentProfileSerializer(serializers.ModelSerializer):
    clinic_name = serializers.CharField(source='clinic.name', read_only=True)
    therapist_name = serializers.CharField(source='assigned_therapist.get_full_name', read_only=True)
    children = ChildSerializer(many=True, read_only=True)
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = ParentProfile
        fields = [
            'id', 'first_name', 'last_name', 'parent_email', 'phone_number',
            'age', 'fscd_approval', 'clinic', 'clinic_name', 'assigned_therapist',
            'therapist_name', 'is_active', 'date_added', 'children', 'children_count'
        ]
        read_only_fields = ['id', 'date_added']

    def get_children_count(self, obj):
        return obj.children.count()


# Speech Therapy Structure Serializers
class SpeechAreaSerializer(serializers.ModelSerializer):
    long_term_goals_count = serializers.SerializerMethodField()

    class Meta:
        model = SpeechArea
        fields = ['id', 'name', 'description', 'is_active', 'long_term_goals_count']

    def get_long_term_goals_count(self, obj):
        return obj.long_term_goals.count()


class LongTermGoalSerializer(serializers.ModelSerializer):
    speech_area_name = serializers.CharField(source='speech_area.name', read_only=True)
    short_term_goals_count = serializers.SerializerMethodField()

    class Meta:
        model = LongTermGoal
        fields = ['id', 'speech_area', 'speech_area_name', 'title', 'description', 'is_active', 'short_term_goals_count']

    def get_short_term_goals_count(self, obj):
        return obj.short_term_goals.count()


class ShortTermGoalSerializer(serializers.ModelSerializer):
    long_term_goal_title = serializers.CharField(source='long_term_goal.title', read_only=True)
    speech_area_name = serializers.CharField(source='long_term_goal.speech_area.name', read_only=True)
    tasks_count = serializers.SerializerMethodField()

    class Meta:
        model = ShortTermGoal
        fields = [
            'id', 'long_term_goal', 'long_term_goal_title', 'speech_area_name',
            'title', 'description', 'is_active', 'tasks_count'
        ]

    def get_tasks_count(self, obj):
        return obj.tasks.count()


class TaskSerializer(serializers.ModelSerializer):
    short_term_goal_title = serializers.CharField(source='short_term_goal.title', read_only=True)
    long_term_goal_title = serializers.CharField(source='short_term_goal.long_term_goal.title', read_only=True)
    speech_area_name = serializers.CharField(source='short_term_goal.long_term_goal.speech_area.name', read_only=True)
    assignments_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            'id', 'short_term_goal', 'short_term_goal_title', 'long_term_goal_title',
            'speech_area_name', 'title', 'description', 'difficulty', 'is_active', 'assignments_count'
        ]

    def get_assignments_count(self, obj):
        return obj.assignments.count()


class AssignmentSerializer(serializers.ModelSerializer):
    child_name = serializers.CharField(source='child.name', read_only=True)
    parent_name = serializers.CharField(source='child.parent.get_full_name', read_only=True)
    therapist_name = serializers.CharField(source='therapist.get_full_name', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_difficulty = serializers.CharField(source='task.difficulty', read_only=True)
    speech_area_name = serializers.CharField(source='task.short_term_goal.long_term_goal.speech_area.name', read_only=True)

    class Meta:
        model = Assignment
        fields = [
            'id', 'child', 'child_name', 'parent_name', 'therapist', 'therapist_name',
            'task', 'task_title', 'task_difficulty', 'speech_area_name',
            'assigned_date', 'due_date', 'completed', 'notes'
        ]
        read_only_fields = ['id', 'assigned_date']


# Task Assignment Serializers
class TaskAssignmentSerializer(serializers.Serializer):
    parent_id = serializers.IntegerField()
    selected_tasks = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="List of task IDs to assign"
    )

    def validate_parent_id(self, value):
        try:
            parent = ParentProfile.objects.get(id=value)
            return value
        except ParentProfile.DoesNotExist:
            raise serializers.ValidationError("Parent profile not found.")

    def validate_selected_tasks(self, value):
        if not value:
            raise serializers.ValidationError("At least one task must be selected.")
        
        # Verify all tasks exist
        existing_tasks = Task.objects.filter(id__in=value, is_active=True)
        if len(existing_tasks) != len(value):
            raise serializers.ValidationError("One or more tasks not found or inactive.")
        
        return value


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value