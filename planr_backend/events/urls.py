from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PrivateEventViewSet, ProfessionalEventViewSet, ServiceViewSet

router = DefaultRouter()
router.register(r'private-events', PrivateEventViewSet, basename='privateevent')
router.register(r'professional-events', ProfessionalEventViewSet, basename='professionalevent')
router.register(r'services', ServiceViewSet, basename='service')

urlpatterns = [
    path('', include(router.urls)),
]
