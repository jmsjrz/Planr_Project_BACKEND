from rest_framework import serializers
from .models import Interest, Profile
from .utils import process_image

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']

class ProfileSerializer(serializers.ModelSerializer):
    interests_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=Interest.objects.all(), write_only=True)

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'gender', 'birth_date', 'profile_image', 'bio', 'interests_ids', 'account_type']

    def validate_profile_image(self, image):
        # Valider que le fichier est bien une image
        if not image.content_type.startswith('image/'):
            raise serializers.ValidationError("Le fichier téléchargé doit être une image.")
        
        # Limiter la taille de l'image à 5 MB
        if image.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("La taille de l'image ne doit pas dépasser 5 MB.")
        
        return image

    def update(self, instance, validated_data):
        # Gérer les centres d'intérêt
        interests = validated_data.pop('interests_ids', None)
        if interests:
            instance.interests.set(interests)
        
        # Gérer l'image de profil
        profile_image = validated_data.get('profile_image')
        if profile_image:
            # Traiter l'image via la fonction utilitaire (redimensionnement et compression)
            validated_data['profile_image'] = process_image(profile_image)
        
        # Mettre à jour les autres champs
        profile = super().update(instance, validated_data)
        
        # Vérifier si le profil est complet après la mise à jour
        profile.check_profile_completion()
        
        return profile

