from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions, generics, status
from django.utils import timezone
from .models import PrivateEvent, EventRegistration, Wishlist
from .serializers import PrivateEventSerializer, EventRegistrationSerializer, WishlistSerializer

class PrivateEventViewSet(viewsets.ModelViewSet):
    """ ViewSet pour gérer les événements particuliers """
    queryset = PrivateEvent.objects.all().select_related('organizer').prefetch_related('participants__profile').filter(date__gte=timezone.now())
    serializer_class = PrivateEventSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location', 'date', 'interests']
    search_fields = ['title', 'description', 'location']
    ordering_fields = ['date', 'category']
    permission_classes = [IsAuthenticated]
      
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
        registration = serializer.save(user=self.request.user)
        registration.event.participants.add(self.request.user)


class WishlistViewSet(viewsets.ModelViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle_wishlist(self, request):
        event_id = request.data.get('event_id')
        event = PrivateEvent.objects.get(id=event_id)
        wishlist, created = Wishlist.objects.get_or_create(user=request.user, event=event)
        
        if not created:
            wishlist.delete()
            return Response({'status': 'removed'}, status=status.HTTP_204_NO_CONTENT)
        
        return Response({'status': 'added'}, status=status.HTTP_201_CREATED)


class MyUpcomingEventsView(generics.ListAPIView):
    """ Vue pour récupérer les événements à venir de l'utilisateur """
    serializer_class = PrivateEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        now = timezone.now()
        # Récupérer les événements futurs auxquels l'utilisateur est inscrit
        return PrivateEvent.objects.filter(participants=user, date__gte=now.date())
