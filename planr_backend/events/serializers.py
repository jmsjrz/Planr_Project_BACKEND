from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import PrivateEvent, ProfessionalEvent, Service, EventRegistration, Wishlist

class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price']


class PrivateEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateEvent
        fields = ['id', 'title', 'description', 'location', 'date', 'time', 'max_participants', 'image']


class ProfessionalEventSerializer(serializers.ModelSerializer):
    services = serializers.PrimaryKeyRelatedField(many=True, queryset=Service.objects.all())

    class Meta:
        model = ProfessionalEvent
        fields = ['id', 'title', 'description', 'location', 'date', 'time', 'max_participants', 'price', 'services', 'image']

from django.contrib.contenttypes.models import ContentType

class EventRegistrationSerializer(serializers.ModelSerializer):
    event_type = serializers.CharField(write_only=True)  # Pour envoyer le type d'événement (private_event ou professional_event)
    event_id = serializers.IntegerField(write_only=True)  # Pour envoyer l'ID de l'événement

    class Meta:
        model = EventRegistration
        fields = ['user', 'event_type', 'event_id', 'registered_at', 'payment_status']
        read_only_fields = ['user', 'registered_at', 'payment_status']

    def create(self, validated_data):
        event_type_str = validated_data.pop('event_type')
        event_id = validated_data.pop('event_id')

        # Trouver le type de contenu correspondant à l'événement (PrivateEvent ou ProfessionalEvent)
        try:
            content_type = ContentType.objects.get(model=event_type_str)
        except ContentType.DoesNotExist:
            raise serializers.ValidationError("Type d'événement invalide.")

        registration = EventRegistration.objects.create(
            user=self.context['request'].user,
            content_type=content_type,
            object_id=event_id,
            **validated_data
        )
        return registration

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['user', 'events']
