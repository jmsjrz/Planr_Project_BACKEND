from django.http import JsonResponse
from .models import User
from .utils import generate_otp, send_email_otp, send_sms_otp
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from rest_framework_simplejwt.tokens import RefreshToken  # Import déplacé en haut

@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def register(request):
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


@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def verify_email_otp(request):
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


@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def verify_otp(request):
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


@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Vérification des champs requis
        if not email or not password:
            return JsonResponse({'error': 'L\'e-mail et le mot de passe sont requis'}, status=400)

        user = get_object_or_404(User, email=email)  # Utilisation de get_object_or_404

        if user.check_password(password):
            refresh = RefreshToken.for_user(user)  # Génération des tokens JWT
            return JsonResponse({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'message': 'Connexion réussie'
            })

        return JsonResponse({'error': 'Mot de passe incorrect'}, status=400)

    return JsonResponse({'error': 'Méthode non autorisée. Utilisez POST.'}, status=405)


@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def request_password_reset(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            return JsonResponse({'error': 'L\'e-mail est requis'}, status=400)

        user = get_object_or_404(User, email=email)  # Utilisation de get_object_or_404
        user.generate_reset_token()  # Génération du jeton de réinitialisation

        reset_link = f"http://localhost:8000/auth/reset-password/{user.reset_token}/"
        send_mail(
            'Réinitialisation de votre mot de passe',
            f'Cliquez sur le lien pour réinitialiser votre mot de passe: {reset_link}',
            'no-reply@planr.dev',
            [email],
        )
        return JsonResponse({'message': 'Un e-mail de réinitialisation a été envoyé.'})


@csrf_exempt # Décorateur pour désactiver la protection CSRF en environnement de développement
def reset_password(request, token):
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
