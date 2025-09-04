from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status


# Common response schemas
error_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error message'),
        'details': openapi.Schema(type=openapi.TYPE_OBJECT, description='Additional error details')
    }
)

success_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Operation success status'),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Success message')
    }
)

# Authentication schemas
login_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['email', 'password'],
    properties={
        'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description='User email address'),
        'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD, description='User password')
    }
)

login_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
        'user': openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                'role_name': openapi.Schema(type=openapi.TYPE_STRING),
            }
        )
    }
)

# Task assignment schemas
task_assignment_request_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    required=['parent_id', 'selected_tasks'],
    properties={
        'parent_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the parent/client'),
        'selected_tasks': openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(type=openapi.TYPE_INTEGER),
            description='List of task IDs to assign'
        )
    }
)

task_assignment_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'success': openapi.Schema(type=openapi.TYPE_BOOLEAN),
        'message': openapi.Schema(type=openapi.TYPE_STRING),
        'child_name': openapi.Schema(type=openapi.TYPE_STRING),
        'assignments_created': openapi.Schema(type=openapi.TYPE_INTEGER)
    }
)

# Dashboard stats schema
dashboard_stats_response_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'total_clinics': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of clinics (superuser only)'),
        'total_therapists': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of therapists'),
        'total_clients': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of clients'),
        'total_assignments': openapi.Schema(type=openapi.TYPE_INTEGER, description='Total number of assignments'),
        'active_assignments': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of active assignments'),
        'clinic_name': openapi.Schema(type=openapi.TYPE_STRING, description='Clinic name (clinic admin only)'),
        'therapist_name': openapi.Schema(type=openapi.TYPE_STRING, description='Therapist name (therapist only)'),
        'parent_name': openapi.Schema(type=openapi.TYPE_STRING, description='Parent name (parent only)'),
    }
)

# Common parameters
speech_area_id_param = openapi.Parameter(
    'speech_area_id',
    openapi.IN_QUERY,
    description='Filter by speech area ID',
    type=openapi.TYPE_INTEGER
)

long_term_goal_id_param = openapi.Parameter(
    'long_term_goal_id',
    openapi.IN_QUERY,
    description='Filter by long-term goal ID',
    type=openapi.TYPE_INTEGER
)

short_term_goal_id_param = openapi.Parameter(
    'short_term_goal_id',
    openapi.IN_QUERY,
    description='Filter by short-term goal ID',
    type=openapi.TYPE_INTEGER
)

difficulty_param = openapi.Parameter(
    'difficulty',
    openapi.IN_QUERY,
    description='Filter by task difficulty',
    type=openapi.TYPE_STRING,
    enum=['beginner', 'intermediate', 'advanced']
)

# Swagger decorators for common endpoints
login_swagger = swagger_auto_schema(
    operation_description="Authenticate user and receive JWT tokens",
    request_body=login_request_schema,
    responses={
        200: login_response_schema,
        400: error_response_schema,
        403: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'error': openapi.Schema(type=openapi.TYPE_STRING),
                'password_reset_required': openapi.Schema(type=openapi.TYPE_BOOLEAN),
                'message': openapi.Schema(type=openapi.TYPE_STRING)
            }
        )
    },
    tags=['Authentication']
)

assign_tasks_swagger = swagger_auto_schema(
    operation_description="Assign multiple tasks to a client",
    request_body=task_assignment_request_schema,
    responses={
        200: task_assignment_response_schema,
        400: error_response_schema,
        403: error_response_schema,
        404: error_response_schema
    },
    tags=['Task Assignment']
)

dashboard_stats_swagger = swagger_auto_schema(
    operation_description="Get dashboard statistics based on user role",
    responses={
        200: dashboard_stats_response_schema,
        401: error_response_schema
    },
    tags=['Dashboard']
)