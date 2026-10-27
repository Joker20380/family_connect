from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from apps.console.views import health

urlpatterns = [path('admin/', admin.site.urls), path('health/', health),
               path('favicon.ico', lambda request: HttpResponse(status=204)), path('', include('apps.console.urls'))]
