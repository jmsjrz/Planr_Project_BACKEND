from rest_framework import serializers
from .models import User, Profile, Interest
from planr_backend.utils import process_image

class UserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle User. Convertit les données du modèle User en JSON.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'is_active']

    def validate_email(self, value):
        """
        Valide que l'adresse e-mail n'est pas vide.
        """
        if not value:
            raise serializers.ValidationError("L'adresse e-mail ne peut pas être vide.")
        return value

    def validate_phone_number(self, value):
        """
        Valide que le numéro de téléphone contient uniquement des chiffres.
        """
        if value and not value.isdigit():
            raise serializers.ValidationError("Le numéro de téléphone doit contenir uniquement des chiffres.")
        return value

class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'name']

class ProfileSerializer(serializers.ModelSerializer):
    interests = InterestSerializer(many=True, read_only=True)
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = Profile
        fields = ['first_name', 'birth_date', 'gender', 'interests', 'profile_picture']

    def update(self, instance, validated_data):
        # Traitement spécial pour l'image
        if 'profile_picture' in validated_data:
            validated_data['profile_picture'] = process_image(validated_data['profile_picture'])
        return super().update(instance, validated_data)
