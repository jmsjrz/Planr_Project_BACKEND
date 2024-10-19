from rest_framework import serializers
from .models import PrivateEvent, ProfessionalEvent, Service

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price']


class PrivateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateEvent
        fields = ['id', 'title', 'description', 'location', 'date', 'time', 'max_participants']


class ProfessionalEventSerializer(serializers.ModelSerializer):
    services = ServiceSerializer(many=True, read_only=True)

    class Meta:
        model = ProfessionalEvent
        fields = ['id', 'title', 'description', 'location', 'date', 'time', 'max_participants', 'price', 'services']
