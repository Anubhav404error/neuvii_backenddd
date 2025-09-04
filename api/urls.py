from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

# Create router for viewsets (if needed in future)
router = DefaultRouter()

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.LoginAPIView.as_view(), name='api_login'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='api_logout'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('auth/change-password/', views.ChangePasswordAPIView.as_view(), name='api_change_password'),
    
    # User management
    path('users/', views.UserListAPIView.as_view(), name='api_user_list'),
    path('users/<int:pk>/', views.UserDetailAPIView.as_view(), name='api_user_detail'),
    path('roles/', views.RoleListAPIView.as_view(), name='api_role_list'),
    
    # Clinic management
    path('clinics/', views.ClinicListAPIView.as_view(), name='api_clinic_list'),
    path('clinics/<int:pk>/', views.ClinicDetailAPIView.as_view(), name='api_clinic_detail'),
    
    # Therapist management
    path('therapists/', views.TherapistProfileListAPIView.as_view(), name='api_therapist_list'),
    path('therapists/<int:pk>/', views.TherapistProfileDetailAPIView.as_view(), name='api_therapist_detail'),
    
    # Client/Parent management
    path('clients/', views.ParentProfileListAPIView.as_view(), name='api_client_list'),
    path('clients/<int:pk>/', views.ParentProfileDetailAPIView.as_view(), name='api_client_detail'),
    
    # Children management
    path('children/', views.ChildListAPIView.as_view(), name='api_child_list'),
    path('children/<int:pk>/', views.ChildDetailAPIView.as_view(), name='api_child_detail'),
    
    # Speech therapy structure
    path('speech-areas/', views.SpeechAreaListAPIView.as_view(), name='api_speech_area_list'),
    path('speech-areas/<int:pk>/', views.SpeechAreaDetailAPIView.as_view(), name='api_speech_area_detail'),
    path('long-term-goals/', views.LongTermGoalListAPIView.as_view(), name='api_long_term_goal_list'),
    path('long-term-goals/<int:pk>/', views.LongTermGoalDetailAPIView.as_view(), name='api_long_term_goal_detail'),
    path('short-term-goals/', views.ShortTermGoalListAPIView.as_view(), name='api_short_term_goal_list'),
    path('short-term-goals/<int:pk>/', views.ShortTermGoalDetailAPIView.as_view(), name='api_short_term_goal_detail'),
    path('tasks/', views.TaskListAPIView.as_view(), name='api_task_list'),
    path('tasks/<int:pk>/', views.TaskDetailAPIView.as_view(), name='api_task_detail'),
    
    # Assignment management
    path('assignments/', views.AssignmentListAPIView.as_view(), name='api_assignment_list'),
    path('assignments/<int:pk>/', views.AssignmentDetailAPIView.as_view(), name='api_assignment_detail'),
    path('assign-tasks/', views.AssignTasksAPIView.as_view(), name='api_assign_tasks'),
    
    # Utility endpoints
    path('profile/', views.user_profile, name='api_user_profile'),
    path('therapist/clients/', views.therapist_clients, name='api_therapist_clients'),
    path('parent/children/', views.parent_children, name='api_parent_children'),
    path('dashboard/stats/', views.DashboardStatsAPIView.as_view(), name='api_dashboard_stats'),
    
    # Include router URLs
    path('', include(router.urls)),
]