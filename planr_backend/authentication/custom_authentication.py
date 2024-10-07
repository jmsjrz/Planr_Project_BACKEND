# authentication/custom_authentication.py

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.utils.translation import gettext_lazy as _

class InactiveUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        """
        Récupère l'utilisateur sans vérifier si is_active est True.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Le token ne contient pas d'identification d'utilisateur reconnaissable."))

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(_("Utilisateur non trouvé."), code="user_not_found")

        # Ne pas vérifier user.is_active ici
        return user
