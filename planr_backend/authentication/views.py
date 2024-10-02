from django.http import JsonResponse
from .models import User, PasswordResetAttempt
from .utils import generate_otp, send_email_otp, send_sms_otp
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta

@csrf_exempt  # Décorateur pour désactiver la protection CSRF en environnement de développement
def register(request):
    """
    Gère l'inscription d'un utilisateur par e-mail ou numéro de téléphone, envoie un OTP pour vérification.

    Args:
        request (HttpRequest): La requête HTTP contenant les données d'inscription.

    Returns:
        JsonResponse: Réponse JSON indiquant le statut de l'inscription et l'envoi de l'OTP.
    """
    if request.method == 'POST':
        data = request.POST
        email = data.get('email')
        phone_number = data.get('phone_number')
        password = data.get('password')

        # Vérification de l'inscription par e-mail
        if email:
            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Un utilisateur avec cet e-mail existe déjà.'}, status=400)
            
            if not password:
                return JsonResponse({'error': 'Un mot de passe est requis pour l\'inscription par e-mail'}, status=400)

            otp = generate_otp()
            send_email_otp(email, otp)  # Envoi de l'OTP par e-mail

            # Création d'un utilisateur non activé
            user = User.objects.create(
                email=email,
                otp=otp,
                otp_created_at=timezone.now(),
                is_active=False
            )
            user.set_password(password)  # Définition du mot de passe
            user.save()
            return JsonResponse({'message': 'Code OTP envoyé par e-mail pour vérification de compte'})

        # Vérification de l'inscription par numéro de téléphone
        if phone_number:
            if User.objects.filter(phone_number=phone_number).exists():
                return JsonResponse({'error': 'Un utilisateur avec ce numéro de téléphone existe déjà.'}, status=400)
            
            otp = generate_otp()
            send_sms_otp(phone_number, otp)  # Envoi de l'OTP par SMS

            # Création de l'utilisateur
            user = User.objects.create(
                phone_number=phone_number,
                otp=otp,
                otp_created_at=timezone.now(),
                is_active=False
            )
            user.save()  # Sauvegarde de l'utilisateur
            return JsonResponse({'message': 'Code OTP envoyé par SMS pour vérification de compte'})

        # Erreur si ni e-mail ni numéro de téléphone n'est fourni
        return JsonResponse({'error': 'Vous devez fournir un e-mail ou un numéro de téléphone'}, status=400)


@csrf_exempt  # Décorateur pour désactiver la protection CSRF en environnement de développement
def verify_email_otp(request):
    """
    Vérifie le code OTP envoyé à l'e-mail de l'utilisateur pour activer son compte.

    Args:
        request (HttpRequest): La requête HTTP contenant l'e-mail et l'OTP.

    Returns:
        JsonResponse: Réponse JSON indiquant le résultat de la vérification.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        otp = request.POST.get('otp')

        user = get_object_or_404(User, email=email)  # Utilisation de get_object_or_404 pour simplifier

        if user.is_otp_valid(otp):
            user.is_active = True
            user.otp = None
            user.otp_created_at = None
            user.save()
            return JsonResponse({'message': 'Vérification de l\'e-mail réussie. Compte activé.'})

        return JsonResponse({'error': 'Le code OTP est invalide ou expiré'}, status=400)


@csrf_exempt  # Décorateur pour désactiver la protection CSRF en environnement de développement
def verify_otp(request):
    """
    Vérifie le code OTP envoyé par SMS à l'utilisateur pour activer son compte.

    Args:
        request (HttpRequest): La requête HTTP contenant le numéro de téléphone et l'OTP.

    Returns:
        JsonResponse: Réponse JSON indiquant le résultat de la vérification.
    """
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        otp = request.POST.get('otp')

        if not otp:
            return JsonResponse({'error': 'Le code OTP est requis'}, status=400)

        user = get_object_or_404(User, phone_number=phone_number)  # Utilisation de get_object_or_404

        if user.is_otp_valid(otp):
            user.is_active = True
            user.otp = None
            user.otp_created_at = None
            user.save()

            refresh = RefreshToken.for_user(user)  # Génération des tokens JWT

            return JsonResponse({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Vérification réussie. Utilisateur activé.'
            })

        return JsonResponse({'error': 'Le code OTP est invalide ou expiré'}, status=400)


@csrf_exempt  # Décorateur pour désactiver la protection CSRF en environnement de développement
def login(request):
    """
    Gère la connexion de l'utilisateur via e-mail et mot de passe.

    Args:
        request (HttpRequest): La requête HTTP contenant l'e-mail et le mot de passe.

    Returns:
        JsonResponse: Réponse JSON avec les jetons d'accès JWT si la connexion réussit.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Vérification des champs requis
        if not email or not password:
            return JsonResponse({'error': 'L\'e-mail et le mot de passe sont requis'}, status=400)

        user = get_object_or_404(User, email=email)  # Utilisation de get_object_or_404

        if user.is_account_locked():
            return JsonResponse({'error': 'Compte verrouillé en raison de multiples tentatives de connexion échouées. Réessayez plus tard.'}, status=403)

        if user.check_password(password):
            user.failed_login_attempts = 0  # Réinitialisation des tentatives échouées
            user.save()
            
            refresh = RefreshToken.for_user(user)  # Génération des tokens JWT
            return JsonResponse({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Connexion réussie'
            })

        # Si le mot de passe est incorrect
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:  # Nombre maximal de tentatives
            user.lock_account(minutes=10)  # Verrouille le compte pendant 10 minutes
            return JsonResponse({'error': 'Compte verrouillé après 5 tentatives échouées. Réessayez dans 10 minutes.'}, status=403)

        user.save()
        return JsonResponse({'error': 'Mot de passe incorrect'}, status=400)


@csrf_exempt  # Décorateur pour désactiver la protection CSRF en environnement de développement
def request_password_reset(request):
    """
    Gère la demande de réinitialisation du mot de passe de l'utilisateur.

    Args:
        request (HttpRequest): La requête HTTP contenant l'e-mail de l'utilisateur.

    Returns:
        JsonResponse: Réponse JSON confirmant l'envoi de l'e-mail de réinitialisation.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            return JsonResponse({'error': 'L\'e-mail est requis'}, status=400)

        user = get_object_or_404(User, email=email)  # Utilisation de get_object_or_404

        # Vérifier la dernière tentative de réinitialisation
        recent_attempt = PasswordResetAttempt.objects.filter(user=user).order_by('-requested_at').first()
        if recent_attempt and recent_attempt.requested_at > timezone.now() - timedelta(minutes=15):
            return JsonResponse({'error': 'Une demande de réinitialisation a déjà été faite récemment. Veuillez patienter 15 minutes.'}, status=429)

        # Enregistrement de la tentative de réinitialisation
        PasswordResetAttempt.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT')
        )

        user.generate_reset_token()  # Génération du jeton de réinitialisation

        reset_link = f"http://localhost:8000/auth/reset-password/{user.reset_token}/"
        send_mail(
            'Réinitialisation de votre mot de passe',
            f'Cliquez sur le lien pour réinitialiser votre mot de passe: {reset_link}',
            'no-reply@planr.dev',
            [email],
        )
        return JsonResponse({'message': 'Un e-mail de réinitialisation a été envoyé.'})


@csrf_exempt  # Décorateur pour désactiver la protection CSRF en environnement de développement
def reset_password(request, token):
    """
    Réinitialise le mot de passe de l'utilisateur à l'aide du jeton fourni.

    Args:
        request (HttpRequest): La requête HTTP contenant le nouveau mot de passe.
        token (str): Le jeton de réinitialisation de mot de passe.

    Returns:
        JsonResponse: Réponse JSON confirmant la réinitialisation du mot de passe.
    """
    if request.method == 'POST':
        user = get_object_or_404(User, reset_token=token)  # Utilisation de get_object_or_404

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
