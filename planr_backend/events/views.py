from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from .models import PrivateEvent, ProfessionalEvent, Service, EventRegistration, Wishlist
from .serializers import PrivateEventSerializer, ProfessionalEventSerializer, ServiceSerializer, EventRegistrationSerializer, WishlistSerializer

class PrivateEventViewSet(viewsets.ModelViewSet):
    """ ViewSet pour gérer les événements particuliers """
    queryset = PrivateEvent.objects.all()
    serializer_class = PrivateEventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'date']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'title']
    permission_classes = [IsAuthenticated]


class ProfessionalEventViewSet(viewsets.ModelViewSet):
    """ ViewSet pour gérer les événements professionnels """
    queryset = ProfessionalEvent.objects.all()
    serializer_class = ProfessionalEventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'date', 'price']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'price', 'title']
    permission_classes = [IsAuthenticated]


class ServiceViewSet(viewsets.ModelViewSet):
    """ ViewSet pour gérer les services associés aux événements professionnels """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

class EventRegistrationViewSet(viewsets.ModelViewSet):
    queryset = EventRegistration.objects.all()
    serializer_class = EventRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Enregistre l'utilisateur et la relation générique vers l'événement
        serializer.save(user=self.request.user)

class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
