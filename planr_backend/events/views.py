from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework import permissions
from .models import PrivateEvent, EventRegistration, Wishlist
from .serializers import PrivateEventSerializer, EventRegistrationSerializer, WishlistSerializer

class PrivateEventViewSet(viewsets.ModelViewSet):
    """ ViewSet pour gérer les événements particuliers """
    queryset = PrivateEvent.objects.all().select_related('organizer').prefetch_related('participants')
    serializer_class = PrivateEventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'date', 'interests']
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'title']
    permission_classes = [IsAuthenticated]  # Permission par défaut pour toutes les actions

    def get_permissions(self):
        """ Applique des permissions différentes selon les actions. """
        if self.action in ['update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsOrganizer]
        return super().get_permissions()

    def perform_create(self, serializer):
        # Assigne l'utilisateur connecté comme organisateur
        serializer.save(organizer=self.request.user)


class IsOrganizer(permissions.BasePermission):
    """ Permission pour vérifier que l'utilisateur est l'organisateur de l'événement. """
    
    def has_object_permission(self, request, view, obj):
        # L'utilisateur doit être l'organisateur de l'événement
        return obj.organizer == request.user



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
