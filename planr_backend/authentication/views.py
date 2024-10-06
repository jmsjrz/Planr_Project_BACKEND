from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from .models import User, PasswordResetAttempt
from .serializers import UserSerializer, PasswordResetAttemptSerializer
from .utils import generate_otp
from .notifications import send_email_otp, send_sms_otp, send_login_alert
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour gérer l'inscription, la vérification OTP, la connexion et la réinitialisation du mot de passe.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    @csrf_exempt  # Si vous utilisez des clients non-web, pensez à la sécurité
    def register(self, request):
        data = request.data
        email = data.get('email')
        phone_number = data.get('phone_number')
        password = data.get('password')

        if email:
            if not password:
                return Response({'error': "Un mot de passe est requis pour l'inscription par e-mail"}, status=status.HTTP_400_BAD_REQUEST)
            response = self.process_registration(email, 'email', password)
        elif phone_number:
            response = self.process_registration(phone_number, 'phone_number')
        else:
            return Response({'error': "Vous devez fournir un e-mail ou un numéro de téléphone"}, status=status.HTTP_400_BAD_REQUEST)

        # Stocker l'ID de l'utilisateur dans la session
        user = User.objects.get(email=email) if email else User.objects.get(phone_number=phone_number)
        request.session['user_id'] = user.id

        return response

    def process_registration(self, identifier, identifier_type, password=None):
        user = User.objects.filter(**{identifier_type: identifier}).first()

        if user and user.otp_created_at and timezone.now() < user.otp_created_at + timedelta(minutes=15):
            return Response({'error': "Vous devez attendre 15 minutes avant de demander un nouveau code OTP."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        otp, hashed_otp = generate_otp()
        if identifier_type == 'email':
            send_email_otp(identifier, otp)
        else:
            send_sms_otp(identifier, otp)

        if not user:
            user = User.objects.create(
                **{identifier_type: identifier},
                otp=hashed_otp,
                otp_created_at=timezone.now(),
                is_active=False
            )
        else:
            user.otp = hashed_otp
            user.otp_created_at = timezone.now()
            user.is_active = False

        if password:
            user.set_password(password)

        user.save()

        return Response({
            'message': f"Code OTP envoyé pour vérification de compte via {identifier_type}."
        })

    @action(detail=False, methods=['post'], url_path='verify-otp', permission_classes=[AllowAny])
    @csrf_exempt  # Si vous utilisez des clients non-web, pensez à la sécurité
    def verify_otp(self, request):
        otp = request.data.get('otp')

        if not otp:
            return Response({'error': "Le code OTP est requis"}, status=status.HTTP_400_BAD_REQUEST)

        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'error': "Session expirée ou invalide. Veuillez recommencer le processus d'inscription."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({'error': "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)

        if user.is_otp_valid(otp):
            user.is_active = True
            user.failed_otp_attempts = 0
            user.save()
            # Nettoyer l'ID de l'utilisateur de la session
            del request.session['user_id']
            return Response({'message': "Compte vérifié avec succès."})

        user.failed_otp_attempts += 1
        if user.failed_otp_attempts >= 3:
            user.lock_account(minutes=10)
            return Response({'error': "Compte verrouillé après plusieurs tentatives OTP infructueuses."}, status=status.HTTP_403_FORBIDDEN)

        user.save()
        return Response({'error': "Le code OTP est invalide ou expiré"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='resend-otp', permission_classes=[AllowAny])
    @csrf_exempt  # Si vous utilisez des clients non-web, pensez à la sécurité
    def resend_otp(self, request):
        user_id = request.session.get('user_id')
        if not user_id:
            return Response({'error': "Session expirée ou invalide. Veuillez recommencer le processus d'inscription."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({'error': "Utilisateur non trouvé"}, status=status.HTTP_404_NOT_FOUND)

        otp, hashed_otp = generate_otp()
        user.otp = hashed_otp
        user.otp_created_at = timezone.now()
        user.save()

        if user.email:
            send_email_otp(user.email, otp)
        elif user.phone_number:
            send_sms_otp(user.phone_number, otp)

        return Response({'message': "Nouveau code OTP envoyé."})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    @csrf_exempt  # Si vous utilisez des clients non-web, pensez à la sécurité
    def login(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': "L'e-mail et le mot de passe sont requis"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, email=email)

        if user.is_account_locked():
            return Response({'error': "Compte verrouillé en raison de multiples tentatives de connexion échouées."}, status=status.HTTP_403_FORBIDDEN)

        if not user.is_active:
            return Response({'error': "Votre compte n'est pas activé. Veuillez vérifier votre e-mail pour activer votre compte."}, status=status.HTTP_403_FORBIDDEN)

        if user.check_password(password):
            return self.process_successful_login(user, request)

        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.lock_account(minutes=10)
            return Response({'error': "Compte verrouillé après 5 tentatives échouées."}, status=status.HTTP_403_FORBIDDEN)

        user.save()
        return Response({'error': "Mot de passe incorrect"}, status=status.HTTP_400_BAD_REQUEST)

    def process_successful_login(self, user, request):
        user.failed_login_attempts = 0
        current_ip = request.META.get('REMOTE_ADDR')
        current_user_agent = request.META.get('HTTP_USER_AGENT')

        if user.last_login_ip != current_ip or user.last_login_user_agent != current_user_agent:
            send_login_alert(user.email, current_ip, current_user_agent)

        user.last_login_ip = current_ip
        user.last_login_user_agent = current_user_agent
        user.save()

        # Stocker l'ID de l'utilisateur dans la session pour maintenir la connexion
        request.session['user_id'] = user.id

        return Response({'message': "Connexion réussie"})

    @action(detail=False, methods=['post'], permission_classes=[AllowAny])
    @csrf_exempt  # Si vous utilisez des clients non-web, pensez à la sécurité
    def logout(self, request):
        # Détruire la session pour déconnecter l'utilisateur
        request.session.flush()
        return Response({'message': "Déconnexion réussie."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='request-password-reset', permission_classes=[AllowAny])
    @csrf_exempt  # Si vous utilisez des clients non-web, pensez à la sécurité
    def request_password_reset(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': "L'e-mail est requis pour réinitialiser le mot de passe."}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(User, email=email)

        recent_attempt = PasswordResetAttempt.objects.filter(user=user).order_by('-requested_at').first()
        if recent_attempt and recent_attempt.requested_at > timezone.now() - timedelta(minutes=15):
            return Response({'error': "Une demande de réinitialisation a déjà été faite récemment. Patientez 15 minutes."}, status=status.HTTP_400_BAD_REQUEST)

        PasswordResetAttempt.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )

        user.generate_reset_token()
        reset_link = f"{settings.BASE_URL}/auth/reset-password/{user.reset_token}/"
        send_mail(
            'Réinitialisation de votre mot de passe',
            f'Cliquez ici pour réinitialiser votre mot de passe: {reset_link}',
            'no-reply@planr.dev',
            [email],
        )
        return Response({'message': "Un e-mail de réinitialisation a été envoyé."})

    @action(detail=False, methods=['post'], url_path='reset-password/(?P<token>[^/.]+)', permission_classes=[AllowAny])
    @csrf_exempt  # Si vous utilisez des clients non-web, pensez à la sécurité
    def reset_password(self, request, token):
        user = get_object_or_404(User, reset_token=token)

        if user.reset_token_expiration < timezone.now():
            return Response({'error': "Le jeton de réinitialisation a expiré"}, status=status.HTTP_400_BAD_REQUEST)

        new_password = request.data.get('new_password')
        if not new_password:
            return Response({'error': "Le nouveau mot de passe est requis"}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiration = None
        user.save()
        return Response({'message': "Mot de passe réinitialisé avec succès."})
