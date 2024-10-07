# views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from datetime import timedelta
from .models import User, PasswordResetAttempt
from .serializers import UserSerializer
from .utils import generate_and_hash_otp, send_email_otp, send_sms_otp
import logging

logger = logging.getLogger(__name__)

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

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer l'inscription, la vérification OTP, la connexion et la réinitialisation du mot de passe.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        data = request.data
        email = data.get('email')
        phone_number = data.get('phone_number')
        password = data.get('password')

        try:
            if email:
                if not password:
                    return Response({'error': "Un mot de passe est requis pour l'inscription par e-mail."}, status=status.HTTP_400_BAD_REQUEST)
                self.process_registration(email, 'email', password)
            elif phone_number:
                self.process_registration(phone_number, 'phone_number')
            else:
                return Response({'error': "Vous devez fournir un e-mail ou un numéro de téléphone."}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(email=email) if email else User.objects.get(phone_number=phone_number)
            guest_token = AccessToken.for_user(user)
            guest_token['role'] = 'guest'
            guest_token['can_verify_otp'] = True
            guest_token.set_exp(lifetime=timedelta(minutes=15))

            return Response({
                'message': "Utilisateur enregistré, un OTP a été envoyé pour vérification.",
                'guest_token': str(guest_token)
            })

        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement : {e}")
            return Response({'error': "Une erreur est survenue, veuillez réessayer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def process_registration(self, identifier, identifier_type, password=None):
        user = User.objects.filter(**{identifier_type: identifier}).first()

        if user and user.otp_created_at and timezone.now() < user.otp_created_at + timedelta(minutes=15):
            raise PermissionDenied("Vous devez attendre 15 minutes avant de demander un nouveau code OTP.")

        otp, hashed_otp = generate_and_hash_otp()
        if identifier_type == 'email':
            send_email_otp(identifier, otp)
        else:
            send_sms_otp(identifier, otp)

        if not user:
            user = User(
                **{identifier_type: identifier},
                otp=hashed_otp,
                otp_created_at=timezone.now(),
                is_active=False
            )
            if password:
                user.set_password(password)
            user.save()
        else:
            user.otp = hashed_otp
            user.otp_created_at = timezone.now()
            user.is_active = False
            if password:
                user.set_password(password)
            user.save()

    @action(
        detail=False,
        methods=['post'],
        url_path='verify-otp',
        permission_classes=[AllowAny],
        authentication_classes=[InactiveUserJWTAuthentication]
    )
    def verify_otp(self, request):
        otp = request.data.get('otp')
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return Response({'error': "Le token JWT est requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            auth = InactiveUserJWTAuthentication()
            validated_token = auth.get_validated_token(auth_header.split(' ')[1])

            if not validated_token.get('can_verify_otp'):
                raise PermissionDenied("Le token ne permet pas de vérifier l'OTP.")

            user = auth.get_user(validated_token)

            if user.is_otp_valid(otp):
                user.is_active = True
                user.failed_otp_attempts = 0
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': "Compte vérifié avec succès.",
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })

            user.failed_otp_attempts += 1
            if user.failed_otp_attempts >= 3:
                user.lock_account(minutes=10)
                return Response({'error': "Compte verrouillé après plusieurs tentatives OTP infructueuses."}, status=status.HTTP_403_FORBIDDEN)

            user.save()
            return Response({'error': "Le code OTP est invalide ou expiré."}, status=status.HTTP_400_BAD_REQUEST)

        except (AuthenticationFailed, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'OTP : {e}")
            return Response({'error': "Une erreur est survenue, veuillez réessayer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(
        detail=False,
        methods=['post'],
        url_path='resend-otp',
        permission_classes=[AllowAny],
        authentication_classes=[InactiveUserJWTAuthentication]
    )
    def resend_otp(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return Response({'error': "Le token JWT est requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            auth = InactiveUserJWTAuthentication()
            validated_token = auth.get_validated_token(auth_header.split(' ')[1])

            if validated_token.get('role') != 'guest':
                return Response({'error': "Permission refusée. Seuls les utilisateurs invités peuvent demander un renvoi d'OTP."}, status=status.HTTP_403_FORBIDDEN)

            user = auth.get_user(validated_token)

            otp, hashed_otp = generate_and_hash_otp()
            user.otp = hashed_otp
            user.otp_created_at = timezone.now()
            user.save()

            if user.email:
                send_email_otp(user.email, otp)
            elif user.phone_number:
                send_sms_otp(user.phone_number, otp)

            return Response({'message': "Nouveau code OTP envoyé."})

        except (AuthenticationFailed, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Erreur lors du renvoi de l'OTP : {e}")
            return Response({'error': "Une erreur est survenue, veuillez réessayer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': "L'e-mail et le mot de passe sont requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = get_object_or_404(User, email=email)

            if user.is_account_locked():
                return Response({'error': "Compte verrouillé en raison de multiples tentatives de connexion échouées."}, status=status.HTTP_403_FORBIDDEN)

            if not user.is_active:
                return Response({'error': "Votre compte n'est pas activé. Veuillez vérifier votre e-mail pour activer votre compte."}, status=status.HTTP_403_FORBIDDEN)

            if user.check_password(password):
                user.failed_login_attempts = 0
                user.save()

                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })

            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.lock_account(minutes=10)
                return Response({'error': "Compte verrouillé après 5 tentatives échouées."}, status=status.HTTP_403_FORBIDDEN)

            user.save()
            return Response({'error': "Mot de passe incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Erreur lors de la connexion : {e}")
            return Response({'error': "Une erreur est survenue, veuillez réessayer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response({'error': "Le token de rafraîchissement est requis pour se déconnecter."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': "Déconnexion réussie."})
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion : {e}")
            return Response({'error': "Une erreur est survenue, veuillez réessayer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='request-password-reset', permission_classes=[AllowAny])
    def request_password_reset(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': "L'e-mail est requis pour réinitialiser le mot de passe."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = get_object_or_404(User, email=email)

            recent_attempt = PasswordResetAttempt.objects.filter(user=user).order_by('-requested_at').first()
            if recent_attempt and recent_attempt.requested_at > timezone.now() - timedelta(minutes=15):
                return Response({'error': "Une demande de réinitialisation a déjà été faite récemment. Patientez 15 minutes."}, status=status.HTTP_403_FORBIDDEN)

            PasswordResetAttempt.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            user.generate_reset_token()
            reset_link = f"{settings.BASE_URL}/auth/reset-password/{user.reset_token}/"

            # Envoi de l'e-mail de réinitialisation
            send_email_otp(user.email, f'Cliquez ici pour réinitialiser votre mot de passe : {reset_link}')
            return Response({'message': "Un e-mail de réinitialisation a été envoyé."})

        except Exception as e:
            logger.error(f"Erreur lors de la demande de réinitialisation de mot de passe : {e}")
            return Response({'error': "Une erreur est survenue, veuillez réessayer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='reset-password/(?P<token>[^/.]+)', permission_classes=[AllowAny])
    def reset_password(self, request, token):
        new_password = request.data.get('new_password')

        if not new_password:
            return Response({'error': "Le nouveau mot de passe est requis."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = get_object_or_404(User, reset_token=token)

            if user.reset_token_expiration < timezone.now():
                return Response({'error': "Le jeton de réinitialisation a expiré."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expiration = None
            user.save()
            return Response({'message': "Mot de passe réinitialisé avec succès."})

        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation du mot de passe : {e}")
            return Response({'error': "Une erreur est survenue, veuillez réessayer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
