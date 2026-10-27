from django.urls import path
from . import views

app_name = 'console'
urlpatterns = [
    path('', views.dashboard, name='dashboard'), path('analytics.json', views.analytics, name='analytics'),
    path('devices/', views.devices, name='devices'), path('devices/refresh/', views.refresh, name='refresh'),
    path('devices/<str:device>/', views.device_detail, name='device'),
    path('payments/', views.payments, name='payments'), path('payments/new/', views.payment_new, name='payment_new'),
    path('payments/<uuid:payment_id>/', views.payment_detail, name='payment'),
    path('operations/', views.operations, name='operations'), path('operations/new/', views.operation_new, name='operation_new'),
    path('operations/<uuid:request_id>/', views.operation_detail, name='operation'),
    path('operations/<uuid:request_id>/preview/', views.operation_preview, name='preview'),
    path('operations/<uuid:request_id>/execute/', views.operation_execute, name='execute'),
    path('operations/<uuid:request_id>/reconcile/', views.operation_reconcile, name='reconcile'),
    path('operations/<uuid:request_id>/receipt.json', views.receipt, name='receipt'),
    path('audit/', views.audit_log, name='audit'), path('releases/', views.releases, name='releases'),
]
