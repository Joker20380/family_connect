from django.urls import path
from . import views
from . import observability

app_name = 'console'
urlpatterns = [
    path('observability/', observability.overview, name='observability'),
    path('inventory/', observability.inventory, name='inventory'),
    path('inventory/<str:pseudonym>/', observability.inventory_device, name='inventory_device'),
    path('servers/<str:source>/', observability.server, name='server'),
    path('telemetry.json', observability.telemetry_json, name='telemetry'),
    path('devices/<str:device>/telemetry/', observability.device_telemetry, name='device_telemetry'),
    path('stop/', observability.stop_screen, name='stop'),
    path('stop/change/', observability.stop_change, name='stop_change'),
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
