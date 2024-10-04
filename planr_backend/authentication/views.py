from django.http import JsonResponse
from .models import User, PasswordResetAttempt
from .utils import generate_otp, send_email_otp, send_sms_otp
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from ratelimit.decorators import ratelimit
import bcrypt

# EXEMPLE DE DECORATEUR DE RATELIMIT
# @ratelimit(key='ip', rate='5/m', method='POST', block=True)  # Limite à 5 requêtes par minute par adresse IP (désactivé pour le développement) -- Utilisez pour la production

@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def verify_otp(request):
    """
    Fusionne la vérification OTP par e-mail et par SMS.
    """
    email = request.POST.get('email')
    phone_number = request.POST.get('phone_number')

    if email:
        return verify_generic_otp(request, identifier=email, id_type='email')
    elif phone_number:
        return verify_generic_otp(request, identifier=phone_number, id_type='phone_number')
    return JsonResponse({'error': 'E-mail ou numéro de téléphone requis'}, status=400)

def verify_generic_otp(request, identifier, id_type):
    """
    Vérifie l'OTP, quel que soit le type (e-mail ou téléphone).

    Args:
        identifier (str): L'e-mail ou numéro de téléphone de l'utilisateur.
        id_type (str): Le type d'identifiant (email ou phone_number).

    Returns:
        JsonResponse: Réponse indiquant si l'OTP est valide.
    """
    otp = request.POST.get('otp')
    if not otp:
        return JsonResponse({'error': 'Le code OTP est requis'}, status=400)

    user = get_object_or_404(User, **{id_type: identifier})

    if user.is_otp_valid(otp):
        user.is_active = True
        user.save()

        refresh = RefreshToken.for_user(user)

        return JsonResponse({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Vérification réussie. Utilisateur activé.'
        })

    return JsonResponse({'error': 'Le code OTP est invalide ou expiré'}, status=400)


@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def register(request):
    """
    Gère l'inscription d'un utilisateur par e-mail ou numéro de téléphone, envoie un OTP pour vérification.
    """
    if request.method == 'POST':
        data = request.POST
        email = data.get('email')
        phone_number = data.get('phone_number')
        password = data.get('password')

        if email:
            if not password:
                return JsonResponse({'error': 'Un mot de passe est requis pour l\'inscription par e-mail'}, status=400)

            return handle_registration(email, 'email', password)

        if phone_number:
            return handle_registration(phone_number, 'phone_number')

        return JsonResponse({'error': 'Vous devez fournir un e-mail ou un numéro de téléphone'}, status=400)


def handle_registration(identifier, identifier_type, password=None):
    """
    Gestion centralisée de l'inscription via e-mail ou téléphone.
    """
    user = User.objects.filter(**{identifier_type: identifier}).first()

    if user:
        if user.otp_created_at and timezone.now() < user.otp_created_at + timedelta(minutes=15):
            return JsonResponse({'error': 'Vous devez attendre 15 minutes avant de demander un nouveau code OTP.'}, status=429)

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
    return JsonResponse({'message': f"Code OTP envoyé pour vérification de compte via {identifier_type}."})


@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def login(request):
    """
    Gère la connexion de l'utilisateur via e-mail et mot de passe.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            return JsonResponse({'error': 'L\'e-mail et le mot de passe sont requis'}, status=400)

        user = get_object_or_404(User, email=email)

        if user.is_account_locked():
            return JsonResponse({'error': 'Compte verrouillé en raison de multiples tentatives de connexion échouées.'}, status=403)

        if user.check_password(password):
            user.failed_login_attempts = 0  

            current_ip = request.META.get('REMOTE_ADDR')
            current_user_agent = request.META.get('HTTP_USER_AGENT')

            if user.last_login_ip != current_ip or user.last_login_user_agent != current_user_agent:
                send_mail(
                    'Nouvelle connexion détectée',
                    f'Une nouvelle connexion a été effectuée sur votre compte depuis l\'adresse IP {current_ip} et l\'appareil {current_user_agent}.',
                    'no-reply@planr.dev',
                    [user.email],
                )

            user.last_login_ip = current_ip
            user.last_login_user_agent = current_user_agent
            user.save()

            refresh = RefreshToken.for_user(user)
            return JsonResponse({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Connexion réussie'
            })

        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.lock_account(minutes=10)  
            return JsonResponse({'error': 'Compte verrouillé après 5 tentatives échouées.'}, status=403)

        user.save()
        return JsonResponse({'error': 'Mot de passe incorrect'}, status=400)


@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def logout(request):
    try:
        refresh_token = request.POST.get('refresh')
        if not refresh_token:
            raise ValueError("Le token de rafraîchissement est manquant")
        
        token = RefreshToken(refresh_token)
        token.blacklist()

        return JsonResponse({'message': 'Déconnexion réussie et token révoqué.'}, status=200)
    
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': 'Erreur lors de la déconnexion. Veuillez réessayer.'}, status=400)


@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def request_password_reset(request):
    try:
        email = request.POST.get('email')
        if not email:
            raise ValueError("L'e-mail est requis pour réinitialiser le mot de passe.")

        user = get_object_or_404(User, email=email)

        recent_attempt = PasswordResetAttempt.objects.filter(user=user).order_by('-requested_at').first()
        if recent_attempt and recent_attempt.requested_at > timezone.now() - timedelta(minutes=15):
            raise ValueError("Une demande de réinitialisation a déjà été faite récemment. Patientez 15 minutes.")

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
        return JsonResponse({'message': 'Un e-mail de réinitialisation a été envoyé.'})

    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': 'Une erreur est survenue. Veuillez réessayer.'}, status=500)


@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def reset_password(request, token):
    """
    Réinitialise le mot de passe de l'utilisateur à l'aide du jeton fourni.
    """
    if request.method == 'POST':
        user = get_object_or_404(User, reset_token=token)

        if user.reset_token_expiration < timezone.now():
            return JsonResponse({'error': 'Le jeton de réinitialisation a expiré'}, status=400)

        new_password = request.POST.get('new_password')
        if not new_password:
            return JsonResponse({'error': 'Le nouveau mot de passe est requis'}, status=400)

        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiration = None
        user.save()
        return JsonResponse({'message': 'Mot de passe réinitialisé avec succès.'})
