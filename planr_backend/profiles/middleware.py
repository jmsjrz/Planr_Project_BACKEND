from django.urls import reverse
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin

class EnsureProfileCompleteMiddleware(MiddlewareMixin):
    def __call__(self, request):
        # Exclure les URLs d'administration
        if request.path.startswith(reverse('admin:index')):
            return self.get_response(request)

        # Si l'utilisateur est authentifié
        if request.user.is_authenticated:
            profile = request.user.profile
            # Vérifier si le profil est incomplet
            if not profile.is_profile_complete:
                # Renvoie une réponse JSON avec un statut 403 au lieu de rediriger
                if request.is_ajax() or request.accepts('application/json'):
                    return Response({'detail': 'Profile incomplete'}, status=403)

        return self.get_response(request)
