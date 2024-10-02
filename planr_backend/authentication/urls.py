# authentication/urls.py
from django.urls import path
from .views import register, verify_otp, request_password_reset, reset_password, login, verify_email_otp
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', register, name='register'),
    path('verify-otp/', verify_otp, name='verify_otp'),
    path('verify-email-otp/', verify_email_otp, name='verify_email_otp'),
    path('request-password-reset/', request_password_reset, name='request_password_reset'),
    path('reset-password/<str:token>/', reset_password, name='reset_password'),
    path('login/', login, name='login'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
