from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PrivateEvent, EventRegistration, Wishlist
from planr_backend.utils import process_image
from authentication.serializers import PublicProfileSerializer
from PIL import Image
import io


class PrivateEventSerializer(serializers.ModelSerializer):
    """ Serializer pour les événements privés. """
    organizer = PublicProfileSerializer(source='organizer.profile', read_only=True) 
    participants = PublicProfileSerializer(many=True, read_only=True)  
    wishlist_count = serializers.SerializerMethodField()

    class Meta:
        model = PrivateEvent
        fields = [
            'id', 
            'title', 
            'description', 
            'location', 
            'date', 
            'time', 
            'max_participants', 
            'image',
            'organizer',
            'participants',
            'wishlist_count'
        ]
    
    def get_wishlist_count(self, obj):
        """ Calcule le nombre de fois que cet événement a été ajouté à la wishlist. """
        return Wishlist.objects.filter(event=obj).count()

    def validate_image(self, image):
        """ Valide que le fichier est bien une image et limite la taille à 5 MB. """
        if not image.content_type.startswith('image/'):
            raise serializers.ValidationError("Le fichier téléchargé doit être une image.")
        if image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("La taille de l'image ne doit pas dépasser 5 MB.")
        return image

    def save(self, **kwargs):
        """ Redimensionne l'image avant de la sauvegarder. """
        image = self.validated_data.get('image')
        if image:
            self.validated_data['image'] = process_image(image)  # Utilisation de la fonction dans utils.py
        return super().save(**kwargs)


class EventRegistrationSerializer(serializers.ModelSerializer):
    """ Serializer pour l'inscription à un événement privé. """
    event_id = serializers.IntegerField(write_only=True)  # ID de l'événement.

    class Meta:
        model = EventRegistration
        fields = ['user', 'event_id', 'registered_at']
        read_only_fields = ['user', 'registered_at']

    def validate(self, data):
        """ Valide que l'utilisateur peut s'inscrire à l'événement. """
        event_id = data.get('event_id')
        user = self.context['request'].user

        if EventRegistration.objects.filter(user=user, event_id=event_id).exists():
            raise serializers.ValidationError("Vous êtes déjà inscrit à cet événement.")

        event = PrivateEvent.objects.get(id=event_id)
        if event.participants.count() >= event.max_participants:
            raise serializers.ValidationError("L'événement a atteint le nombre maximum de participants.")

        return data

    def create(self, validated_data):
        """ Crée une nouvelle inscription à un événement privé. """
        event_id = validated_data.pop('event_id')

        registration = EventRegistration.objects.create(
            user=self.context['request'].user,
            event_id=event_id,
            **validated_data
        )
        return registration



class WishlistSerializer(serializers.ModelSerializer):
    """ Serializer pour la wishlist des événements privés. """
    class Meta:
        model = Wishlist
        fields = ['user', 'event']
