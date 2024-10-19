from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from authentication.views import UserViewSet


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include('authentication.urls')),
    path('', include('events.urls')),
    path('admin/', admin.site.urls),
]
