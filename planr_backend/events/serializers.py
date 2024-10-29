from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PrivateEvent, EventRegistration, Wishlist
from planr_backend.utils import process_image
from authentication.serializers import PublicProfileSerializer
from PIL import Image
from datetime import datetime
import io


class PrivateEventSerializer(serializers.ModelSerializer):
    """ Serializer pour les événements privés. """
    organizer = PublicProfileSerializer(source='organizer.profile', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    category = serializers.CharField(write_only=True)
    participants = serializers.SerializerMethodField()
    wishlist_count = serializers.SerializerMethodField()
    is_wishlisted = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()

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
            'wishlist_count',
            'is_wishlisted',
            'is_registered',
            'category',
            'category_display'
        ]
    
    def get_wishlist_count(self, obj):
        """ Calcule le nombre de fois que cet événement a été ajouté à la wishlist. """
        return Wishlist.objects.filter(event=obj).count()

    def get_is_wishlisted(self, obj):
        """ Vérifie si l'utilisateur actuel a ajouté cet événement à sa wishlist. """
        user = self.context['request'].user  # Récupère l'utilisateur courant
        if not user.is_authenticated:
            return False  # Si l'utilisateur n'est pas authentifié, retourne False
        return Wishlist.objects.filter(user=user, event=obj).exists()

    def get_is_registered(self, obj):
        """ Vérifie si l'utilisateur actuel est inscrit à cet événement. """
        user = self.context['request'].user  # Récupère l'utilisateur courant
        if not user.is_authenticated:
            return False  # Si l'utilisateur n'est pas authentifié, retourne False
        return EventRegistration.objects.filter(user=user, event=obj).exists()
    
    def get_participants(self, obj):
        """ Retourne les participants avec un chemin complet pour leur photo de profil """
        request = self.context.get('request')
        participants = obj.participants.all()
        
        serialized_participants = []
        for participant in participants:
            profile = participant.profile
            profile_picture_url = profile.profile_picture.url if profile.profile_picture else '/default-avatar.png'
            
            if request:
                profile_picture_url = request.build_absolute_uri(profile_picture_url)
            
            serialized_participants.append({
                'firstName': profile.first_name,
                'profilePicture': profile_picture_url
            })
        
        return serialized_participants

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

        event_start = datetime.combine(event.date, event.time)
        if event_start <= datetime.now():
            raise serializers.ValidationError("Il n'est plus possible de s'inscrire à cet événement car il a déjà commencé.")

        return data

    def create(self, validated_data):
        """ Crée une nouvelle inscription à un événement privé. """
        event_id = validated_data.pop('event_id')
        user = self.context['request'].user
        registration = EventRegistration.objects.create(
            user=user,
            event_id=event_id,
        )
        return registration



class WishlistSerializer(serializers.ModelSerializer):
    """ Serializer pour la wishlist des événements privés. """
    class Meta:
        model = Wishlist
        fields = ['user', 'event']
