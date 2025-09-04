import django_filters
from therapy.models import Assignment, Task, ParentProfile, TherapistProfile
from clinic.models import Clinic


class AssignmentFilter(django_filters.FilterSet):
    """Filter assignments by various criteria"""
    completed = django_filters.BooleanFilter()
    therapist_id = django_filters.NumberFilter(field_name='therapist__id')
    child_id = django_filters.NumberFilter(field_name='child__id')
    parent_id = django_filters.NumberFilter(field_name='child__parent__id')
    difficulty = django_filters.CharFilter(field_name='task__difficulty')
    speech_area = django_filters.CharFilter(field_name='task__short_term_goal__long_term_goal__speech_area__name', lookup_expr='icontains')
    assigned_date_from = django_filters.DateFilter(field_name='assigned_date', lookup_expr='gte')
    assigned_date_to = django_filters.DateFilter(field_name='assigned_date', lookup_expr='lte')
    due_date_from = django_filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_date_to = django_filters.DateFilter(field_name='due_date', lookup_expr='lte')

    class Meta:
        model = Assignment
        fields = ['completed', 'therapist_id', 'child_id', 'parent_id', 'difficulty', 'speech_area']


class TaskFilter(django_filters.FilterSet):
    """Filter tasks by various criteria"""
    difficulty = django_filters.CharFilter()
    speech_area_id = django_filters.NumberFilter(field_name='short_term_goal__long_term_goal__speech_area__id')
    long_term_goal_id = django_filters.NumberFilter(field_name='short_term_goal__long_term_goal__id')
    short_term_goal_id = django_filters.NumberFilter(field_name='short_term_goal__id')
    title = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Task
        fields = ['difficulty', 'speech_area_id', 'long_term_goal_id', 'short_term_goal_id', 'title']


class ParentProfileFilter(django_filters.FilterSet):
    """Filter parent profiles by various criteria"""
    clinic_id = django_filters.NumberFilter(field_name='clinic__id')
    therapist_id = django_filters.NumberFilter(field_name='assigned_therapist__id')
    fscd_approval = django_filters.CharFilter()
    age_min = django_filters.NumberFilter(field_name='age', lookup_expr='gte')
    age_max = django_filters.NumberFilter(field_name='age', lookup_expr='lte')
    name = django_filters.CharFilter(method='filter_by_name')

    class Meta:
        model = ParentProfile
        fields = ['clinic_id', 'therapist_id', 'fscd_approval', 'age_min', 'age_max']

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            models.Q(first_name__icontains=value) | 
            models.Q(last_name__icontains=value)
        )


class TherapistProfileFilter(django_filters.FilterSet):
    """Filter therapist profiles by various criteria"""
    clinic_id = django_filters.NumberFilter(field_name='clinic__id')
    name = django_filters.CharFilter(method='filter_by_name')

    class Meta:
        model = TherapistProfile
        fields = ['clinic_id']

    def filter_by_name(self, queryset, name, value):
        return queryset.filter(
            models.Q(first_name__icontains=value) | 
            models.Q(last_name__icontains=value)
        )