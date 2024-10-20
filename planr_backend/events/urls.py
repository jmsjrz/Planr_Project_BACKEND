from django.urls import path, include
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import PrivateEventViewSet, ProfessionalEventViewSet, ServiceViewSet, EventRegistrationViewSet, WishlistViewSet
from django.conf import settings

router = DefaultRouter()
router.register(r'private-events', PrivateEventViewSet, basename='privateevent')
router.register(r'professional-events', ProfessionalEventViewSet, basename='professionalevent')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'registrations', EventRegistrationViewSet, basename='registration')
router.register(r'wishlists', WishlistViewSet, basename='wishlist')

urlpatterns = [
    path('', include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
