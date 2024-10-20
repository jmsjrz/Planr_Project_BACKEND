from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.exceptions import PermissionDenied

class EnsureProfileCompleteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si l'utilisateur est authentifié
        if request.user.is_authenticated:
            profile = request.user.profile
            # Vérifier si le profil est incomplet
            if not profile.is_profile_complete:
                # Bloquer l'accès aux autres routes jusqu'à ce que le profil soit complété
                raise PermissionDenied("Vous devez compléter votre profil avant de continuer.")
        return self.get_response(request)
