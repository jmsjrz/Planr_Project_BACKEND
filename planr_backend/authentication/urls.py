# urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ProfileViewSet, CheckProfileCompletionViewSet
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/profile/', ProfileViewSet.as_view({'get': 'retrieve', 'put': 'update'}), name='user-profile'),
    path('users/profile/completion/', CheckProfileCompletionViewSet.as_view(), name='check_profile_completion'),
    path('', include(router.urls)),
]
