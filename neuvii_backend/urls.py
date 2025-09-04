"""
URL configuration for neuvii_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from .admin_sites import neuvii_admin_site
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

def redirect_to_login(request):
    return redirect('/auth/login/')

# Swagger/OpenAPI schema
schema_view = get_schema_view(
    openapi.Info(
        title="Neuvii Therapy Management API",
        default_version='v1',
        description="""
        Comprehensive API for Neuvii Therapy Management System
        
        ## Authentication
        This API uses JWT (JSON Web Tokens) for authentication. To access protected endpoints:
        1. Login using `/api/auth/login/` to get access and refresh tokens
        2. Include the access token in the Authorization header: `Bearer <access_token>`
        3. Use `/api/auth/refresh/` to refresh expired tokens
        
        ## User Roles
        - **Super Admin**: Full system access
        - **Clinic Admin**: Manage their clinic, therapists, and clients
        - **Therapist**: Manage assigned clients and tasks
        - **Parent**: View their children's assignments and progress
        
        ## Key Features
        - Role-based access control
        - Comprehensive therapy management
        - Task assignment workflow
        - Real-time dashboard statistics
        """,
        terms_of_service="https://www.neuvii.com/terms/",
        contact=openapi.Contact(email="support@neuvii.com"),
        license=openapi.License(name="Proprietary License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)
# Custom admin site header
admin.site.site_header = 'Neuvii Administration'
admin.site.site_title = 'Neuvii Administration'
admin.site.index_title = 'Site Administration'

urlpatterns = [
    path("admin/", neuvii_admin_site.urls),
    path("auth/", include('users.urls')),
    path("therapy/", include('therapy.urls')),
    path("api/", include('api.urls')),
    
    # Swagger/OpenAPI documentation
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    path('', redirect_to_login),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)