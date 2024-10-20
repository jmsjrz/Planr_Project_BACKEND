from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfileViewSet, InterestViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'interests', InterestViewSet, basename='interest')

urlpatterns = [
    path('', include(router.urls)),
]
