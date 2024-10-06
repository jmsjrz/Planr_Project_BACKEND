from rest_framework import serializers
from .models import User, PasswordResetAttempt

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

class PasswordResetAttemptSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour le modèle PasswordResetAttempt. 
    Permet de suivre les tentatives de réinitialisation de mot de passe.
    """
    class Meta:
        model = PasswordResetAttempt
        fields = ['id', 'user', 'requested_at', 'ip_address', 'user_agent']
