from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from apps.console.views import health
from apps.fleet.views import console as fleet_console

urlpatterns = [path('admin/', admin.site.urls), path('health/', health), path('fleet/', fleet_console, name='fleet-console'),
               path('favicon.ico', lambda request: HttpResponse(status=204)), path('', include('apps.console.urls'))]
