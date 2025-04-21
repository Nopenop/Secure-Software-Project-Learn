"""
URL configuration for serverMonitoring project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from components import user_services, web_services, monitoring_services, email_services

urlpatterns = [
    path('v2/api/create-user/', user_services.createUser),
    path('v2/api/create-endpoint/', monitoring_services.createEndpoint),
    path('v2/api/account-login/', web_services.accountLogin),
    path('v2/api/user-endpoints/', web_services.getUserEndpoints),
    path('v2/api/edit-endpoint/', monitoring_services.editEndpoint),
    path('v2/api/delete-endpoint/', monitoring_services.deleteEndpoint),
    path("v2/api/update-status/", monitoring_services.update_status),
    path("v2/api/email/", email_services.send_mail_page),
]
