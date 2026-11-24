from django.urls import path
from . import views
from . import observability
from . import objects
from . import support
from . import system_messages

app_name = 'console'
urlpatterns = [
    path('system-messages/', system_messages.index, name='system_messages'),
    path('system-messages/new/', system_messages.compose, name='system_message_new'),
    path('system-messages/preview/', system_messages.preview, name='system_message_preview'),
    path('system-messages/<uuid:ident>/', system_messages.detail, name='system_message'),
    path('system-messages/<uuid:ident>/send/', system_messages.send, name='system_message_send'),
    path('messages/', support.inbox, name='support_inbox'),
    path('inventory/<str:pseudonym>/messages/', support.history, name='support_history'),
    path('inventory/<str:pseudonym>/messages/send/', support.send, name='support_send'),
    path('subscriptions/', observability.subscriptions, name='subscriptions'),
    path('observability/', observability.overview, name='observability'),
    path('inventory/', objects.devices, name='inventory'),
    path('inventory/<str:pseudonym>/', objects.device, name='inventory_device'),
    path('servers/', objects.servers, name='servers'),
    path('servers/<str:source>/', objects.server, name='server'),
    path('events/', objects.events, name='events'),
    path('telemetry.json', observability.telemetry_json, name='telemetry'),
    path('devices/<str:device>/telemetry/', observability.device_telemetry, name='device_telemetry'),
    path('stop/', observability.stop_screen, name='stop'),
    path('stop/change/', observability.stop_change, name='stop_change'),
    path('', objects.overview, name='dashboard'),
    path('demo/', views.dashboard, name='demo_dashboard'), path('analytics.json', views.analytics, name='analytics'),
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
