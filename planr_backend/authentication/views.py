from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.http import Http404
from .models import User, PasswordResetAttempt, Profile
from .serializers import PrivateUserSerializer, PublicUserSerializer, PrivateProfileSerializer
from .utils import generate_and_hash_otp, send_email_otp, send_sms_otp, send_email
from .messages import ErrorMessages, SuccessMessages  # Centralisation des messages
import logging


logger = logging.getLogger(__name__)


class InactiveUserJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(ErrorMessages.TOKEN_INVALID)

        try:
            user = self.user_model.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except self.user_model.DoesNotExist:
            raise AuthenticationFailed(ErrorMessages.USER_NOT_FOUND)

        return user


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = PrivateUserSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def register(self, request):
        data = request.data
        email = data.get('email')
        phone_number = data.get('phone_number')
        password = data.get('password')

        try:
            if email:
                if User.objects.filter(email=email).exists():
                    return Response({'error': ErrorMessages.EMAIL_ALREADY_EXISTS}, status=status.HTTP_400_BAD_REQUEST)
                if not password:
                    return Response({'error': ErrorMessages.PASSWORD_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)
                self.process_registration(email, 'email', password)

            elif phone_number:
                if User.objects.filter(phone_number=phone_number).exists():
                    return Response({'error': ErrorMessages.PHONE_ALREADY_EXISTS}, status=status.HTTP_400_BAD_REQUEST)
                self.process_registration(phone_number, 'phone_number')

            else:
                return Response({'error': ErrorMessages.LOGIN_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(email=email) if email else User.objects.get(phone_number=phone_number)
            guest_token = AccessToken.for_user(user)
            guest_token['role'] = 'guest'
            guest_token['can_verify_otp'] = True
            guest_token.set_exp(lifetime=timedelta(minutes=15))

            return Response({
                'message': SuccessMessages.REGISTRATION_SUCCESS,
                'guest_token': str(guest_token)
            }, status=status.HTTP_201_CREATED)

        except PermissionDenied as e:
            logger.error(f"Erreur lors de l'enregistrement : {e}")
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement : {e}")
            return Response({'error': ErrorMessages.UNAUTHORIZED_ACCESS}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def process_registration(self, identifier, identifier_type, password=None):
        user = User.objects.filter(**{identifier_type: identifier}).first()

        if user and user.otp_created_at and timezone.now() < user.otp_created_at + timedelta(minutes=15):
            raise PermissionDenied(ErrorMessages.OTP_RESEND_LIMIT)

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

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def check_registration(self, request):
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')

        user = None
        if email:
            user = User.objects.filter(email=email).first()
        elif phone_number:
            user = User.objects.filter(phone_number=phone_number).first()

        if user and user.otp_created_at and timezone.now() < user.otp_created_at + timedelta(minutes=15):
            guest_token = AccessToken.for_user(user)
            guest_token['role'] = 'guest'
            guest_token['can_verify_otp'] = True
            guest_token.set_exp(lifetime=timedelta(minutes=15))

            return Response({
                'message': SuccessMessages.OTP_RESEND_SUCCESS,
                'guest_token': str(guest_token)
            }, status=status.HTTP_200_OK)

        return Response({'error': ErrorMessages.USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='verify-otp', permission_classes=[AllowAny], authentication_classes=[InactiveUserJWTAuthentication])
    def verify_otp(self, request):
        otp = request.data.get('otp')
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return Response({'error': ErrorMessages.JWT_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        try:
            auth = InactiveUserJWTAuthentication()
            validated_token = auth.get_validated_token(auth_header.split(' ')[1])

            if not validated_token.get('can_verify_otp'):
                raise PermissionDenied(ErrorMessages.UNAUTHORIZED_ACCESS)

            user = auth.get_user(validated_token)

            if user.is_account_locked():
                return Response({'error': ErrorMessages.ACCOUNT_LOCKED}, status=status.HTTP_403_FORBIDDEN)

            if user.is_otp_valid(otp):
                user.is_active = True
                user.failed_otp_attempts = 0
                user.save()
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': SuccessMessages.OTP_VERIFICATION_SUCCESS,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                })

            user.failed_otp_attempts += 1
            if user.failed_otp_attempts >= 3:
                user.lock_account(minutes=10)
                return Response({'error': ErrorMessages.OTP_MAX_ATTEMPTS}, status=status.HTTP_403_FORBIDDEN)

            user.save()
            return Response({'error': ErrorMessages.OTP_INVALID}, status=status.HTTP_400_BAD_REQUEST)

        except (AuthenticationFailed, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'OTP : {e}")
            return Response({'error': ErrorMessages.UNAUTHORIZED_ACCESS}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='resend-otp', permission_classes=[AllowAny], authentication_classes=[InactiveUserJWTAuthentication])
    def resend_otp(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return Response({'error': ErrorMessages.JWT_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        try:
            auth = InactiveUserJWTAuthentication()
            validated_token = auth.get_validated_token(auth_header.split(' ')[1])

            if validated_token.get('role') != 'guest':
                return Response({'error': ErrorMessages.INVALID_CREDENTIALS}, status=status.HTTP_403_FORBIDDEN)

            user = auth.get_user(validated_token)

            if user.otp_created_at and timezone.now() < user.otp_created_at + timedelta(minutes=15):
                return Response({'error': ErrorMessages.OTP_RESEND_LIMIT}, status=status.HTTP_403_FORBIDDEN)

            otp, hashed_otp = generate_and_hash_otp()
            user.otp = hashed_otp
            user.otp_created_at = timezone.now()
            user.save()

            if user.email:
                send_email_otp(user.email, otp)
            elif user.phone_number:
                send_sms_otp(user.phone_number, otp)

            return Response({'message': SuccessMessages.OTP_RESEND_SUCCESS})

        except (AuthenticationFailed, PermissionDenied) as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            logger.error(f"Erreur lors du renvoi de l'OTP : {e}")
            return Response({'error': ErrorMessages.UNAUTHORIZED_ACCESS}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    def login(self, request):
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        try:
            if not email and not phone_number:
                return Response({'error': ErrorMessages.LOGIN_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

            user = None
            if email:
                user = User.objects.filter(email=email).first()
                if not user:
                    return Response({'error': ErrorMessages.USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)
            elif phone_number:
                user = User.objects.filter(phone_number=phone_number).first()
                if not user:
                    return Response({'error': ErrorMessages.USER_NOT_FOUND}, status=status.HTTP_404_NOT_FOUND)

            if password:
                if user.is_account_locked():
                    return Response({'error': ErrorMessages.ACCOUNT_LOCKED}, status=status.HTTP_403_FORBIDDEN)

                if not user.is_active:
                    return Response({'error': ErrorMessages.USER_INACTIVE}, status=status.HTTP_403_FORBIDDEN)

                if user.check_password(password):
                    user.failed_login_attempts = 0
                    user.save()

                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'message': SuccessMessages.LOGIN_SUCCESS,
                        'refresh': str(refresh),
                        'access': str(refresh.access_token),
                    }, status=status.HTTP_200_OK)

                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.lock_account(minutes=10)
                    return Response({'error': ErrorMessages.ACCOUNT_LOCKED}, status=status.HTTP_403_FORBIDDEN)

                user.save()
                return Response({'error': ErrorMessages.PASSWORD_MISMATCH}, status=status.HTTP_401_UNAUTHORIZED)

            otp, hashed_otp = generate_and_hash_otp()
            if user.email:
                send_email_otp(user.email, otp)
            elif user.phone_number:
                send_sms_otp(user.phone_number, otp)

            user.otp = hashed_otp
            user.otp_created_at = timezone.now()
            user.save()

            guest_token = AccessToken.for_user(user)
            guest_token['role'] = 'guest'
            guest_token['can_verify_otp'] = True
            guest_token.set_exp(lifetime=timedelta(minutes=15))

            return Response({
                'message': SuccessMessages.OTP_SENT,
                'guest_token': str(guest_token)
            }, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return Response({'error': str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de la connexion : {e}")
            return Response({'error': ErrorMessages.UNAUTHORIZED_ACCESS}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response({'error': ErrorMessages.JWT_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': SuccessMessages.LOGOUT_SUCCESS})
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion : {e}")
            return Response({'error': ErrorMessages.UNAUTHORIZED_ACCESS}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='request-password-reset', permission_classes=[AllowAny])
    def request_password_reset(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': ErrorMessages.LOGIN_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = get_object_or_404(User, email=email)

            recent_attempt = PasswordResetAttempt.objects.filter(user=user).order_by('-requested_at').first()
            if recent_attempt and recent_attempt.requested_at > timezone.now() - timedelta(minutes=15):
                return Response({'error': ErrorMessages.RESET_LIMIT_REACHED}, status=status.HTTP_403_FORBIDDEN)

            PasswordResetAttempt.objects.create(
                user=user,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT')
            )

            user.generate_reset_token()
            reset_link = f"{settings.FRONTEND_URL}/reset-password/{user.reset_token}/"

            send_email(user.email, f'Cliquez ici pour réinitialiser votre mot de passe : {reset_link}', [user.email])
            return Response({'message': SuccessMessages.PASSWORD_RESET_EMAIL_SENT})

        except Exception as e:
            logger.error(f"Erreur lors de la demande de réinitialisation de mot de passe : {e}")
            return Response({'error': ErrorMessages.UNAUTHORIZED_ACCESS}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='reset-password/(?P<token>[^/.]+)', permission_classes=[AllowAny])
    def reset_password(self, request, token):
        new_password = request.data.get('new_password')

        if not new_password:
            return Response({'error': ErrorMessages.PASSWORD_REQUIRED}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = get_object_or_404(User, reset_token=token)

            if user.reset_token_expiration < timezone.now():
                return Response({'error': ErrorMessages.RESET_TOKEN_INVALID}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.reset_token = None
            user.reset_token_expiration = None
            user.save()

            return Response({'message': SuccessMessages.PASSWORD_RESET_SUCCESS}, status=status.HTTP_200_OK)

        except Http404:
            return Response({'error': ErrorMessages.RESET_TOKEN_INVALID}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation du mot de passe : {e}")
            return Response({'error': ErrorMessages.UNAUTHORIZED_ACCESS}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def retrieve(self, request):
        """Récupérer le profil de l'utilisateur connecté."""
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = PrivateProfileSerializer(profile)
        return Response(serializer.data)

    def update(self, request):
        """Mettre à jour le profil de l'utilisateur connecté."""
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = PrivateProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckProfileCompletionViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Récupérer le profil de l'utilisateur connecté
        try:
            profile = request.user.profile
            return Response({'is_profile_complete': profile.is_profile_complete})
        except Profile.DoesNotExist:
            return Response({'is_profile_complete': False}, status=status.HTTP_200_OK)
