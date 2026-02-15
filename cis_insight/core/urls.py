"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.urls import path
from . import views
from users import views as users_views
from news import views as news_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.render_landing_page, name='landing_page'),
    path('sign_up/<str:verification_code>/', users_views.render_sign_up_page, name='sign_up'),
    path('sign_in/', users_views.render_sign_in_page, name='sign_in'),
    path('dashboard/', news_views.render_dashboard_page, name='dashboard'),
    path('logout/', users_views.render_logout_page, name='logout'),
    path('news_settings/', users_views.render_news_settings_page, name='news_settings'),
    path('display_settings/', users_views.render_display_settings_page, name='display_settings'),
    path('account_settings/', users_views.render_account_settings_page, name='account_settings'),
    path('password_change/<str:verification_code>/', users_views.render_password_change_page, name='password_change'),
    path('error/', views.render_error_page, name='error'),
    path('admin/', users_views.render_admin_page, name='admin'),
    path('api/pre_sign_up/', views.pre_sign_up, name='api_pre_sign_up'),
    path('api/sign_up/', users_views.sign_up, name='api_sign_up'),
    path('api/sign_in/', users_views.sign_in, name='api_sign_in'),
    path('api/news_settings/', users_views.news_settings, name='api_news_settings'),
    path('api/account_settings/', users_views.account_settings, name='api_account_settings'),
    path('api/pre_password_change/', users_views.pre_password_change, name='api_pre_password_change'),
    path('api/password_change/<str:verification_code>/', users_views.password_change, name='api_password_change'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

