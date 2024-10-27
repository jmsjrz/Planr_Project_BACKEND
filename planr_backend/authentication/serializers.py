from rest_framework import serializers
from .models import User, Profile, Interest
from planr_backend.utils import process_image


class InterestSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour les centres d'intérêt.
    """
    class Meta:
        model = Interest
        fields = ['id', 'name']


class PrivateUserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'utilisateur avec des informations privées (email, téléphone, etc.).
    Utilisé pour l'affichage du compte utilisateur.
    """
    profile = serializers.StringRelatedField()  # Affiche le lien vers le profil de l'utilisateur

    class Meta:
        model = User
        fields = ['id', 'email', 'phone_number', 'is_active', 'profile']  # Affichage du profil lié
        read_only_fields = ['id', 'is_active']

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


class PublicUserSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour l'utilisateur avec des informations publiques via le profil.
    Utilisé pour l'affichage dans des événements ou d'autres contextes publics.
    """
    profile = serializers.StringRelatedField()  # Affiche le lien vers le profil de l'utilisateur

    class Meta:
        model = User
        fields = ['id', 'profile']
        read_only_fields = ['id']


class PrivateProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le profil utilisateur avec des informations privées.
    """
    interests = InterestSerializer(many=True, read_only=True)
    profile_picture = serializers.ImageField(required=False)

    class Meta:
        model = Profile
        fields = ['first_name', 'birth_date', 'gender', 'interests', 'profile_picture']
        read_only_fields = ['profile_picture']

    def update(self, instance, validated_data):
        """
        Traitement spécial pour l'image du profil lors de la mise à jour.
        """
        # Vérifiez si le champ profile_picture est présent et traitez-le
        if 'profile_picture' in validated_data:
            validated_data['profile_picture'] = process_image(validated_data['profile_picture'])
            
        return super().update(instance, validated_data)

class PublicProfileSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le profil public de l'utilisateur.
    """
    class Meta:
        model = Profile
        fields = ['first_name', 'profile_picture']


