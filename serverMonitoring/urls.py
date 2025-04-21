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
    path("v2/api/update-status", monitoring_services.update_status),
    path("v2/api/email", email_services.send_mail_page),
]
