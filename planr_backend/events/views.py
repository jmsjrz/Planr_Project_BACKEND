from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import PrivateEvent, ProfessionalEvent, Service
from .serializers import PrivateEventSerializer, ProfessionalEventSerializer, ServiceSerializer

class PrivateEventViewSet(viewsets.ModelViewSet):
    """ ViewSet pour gérer les événements particuliers """
    queryset = PrivateEvent.objects.all()
    serializer_class = PrivateEventSerializer
    permission_classes = [IsAuthenticated]


class ProfessionalEventViewSet(viewsets.ModelViewSet):
    """ ViewSet pour gérer les événements professionnels """
    queryset = ProfessionalEvent.objects.all()
    serializer_class = ProfessionalEventSerializer
    permission_classes = [IsAuthenticated]


class ServiceViewSet(viewsets.ModelViewSet):
    """ ViewSet pour gérer les services associés aux événements professionnels """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]
