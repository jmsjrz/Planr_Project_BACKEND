from django.http import JsonResponse
from .models import User
from .utils import generate_otp, send_email_otp, send_sms_otp
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404

@csrf_exempt # Désactive la protection CSRF pour cette vue en environnement de développement
def register(request):
    if request.method == 'POST':
        data = request.POST
        email = data.get('email')
        phone_number = data.get('phone_number')
        
        if email:
            otp = generate_otp()
            send_email_otp(email, otp)
            
            # Créer et sauvegarder l'utilisateur
            user = User.objects.create(
                email=email,
                otp=otp,
                otp_created_at=timezone.now(),
                is_active=False
            )
            user.save()  # Assurez-vous que l'utilisateur est bien sauvegardé
            return JsonResponse({'message': 'Code OTP envoyé par e-mail'})
        
        elif phone_number:
            otp = generate_otp()
            send_sms_otp(phone_number, otp)
            
            # Créer et sauvegarder l'utilisateur
            user = User.objects.create(
                phone_number=phone_number,
                otp=otp,
                otp_created_at=timezone.now(),
                is_active=False
            )
            user.save()  # Assurez-vous que l'utilisateur est bien sauvegardé
            return JsonResponse({'message': 'Code OTP envoyé par SMS'})
        
        return JsonResponse({'error': 'Vous devez fournir un e-mail ou un numéro de téléphone'}, status=400)


@csrf_exempt # Désactive la protection CSRF pour cette vue en environnement de développement
def verify_otp(request):
    if request.method == 'POST':
        data = request.POST
        email = data.get('email')
        phone_number = data.get('phone_number')
        otp = data.get('otp')

        if not otp:
            return JsonResponse({'error': 'Le code OTP est requis'}, status=400)

        user = None
        if email:
            user = get_object_or_404(User, email=email)
        elif phone_number:
            user = get_object_or_404(User, phone_number=phone_number)
        else:
            return JsonResponse({'error': 'Vous devez fournir un email ou un numéro de téléphone'}, status=400)

        if user.is_otp_valid(otp):
            user.is_active = True  # Activez l'utilisateur après une vérification réussie
            user.otp = None  # Effacez l'OTP après utilisation
            user.otp_created_at = None
            user.save()
            return JsonResponse({'message': 'Vérification réussie. Utilisateur activé.'})
        else:
            return JsonResponse({'error': 'Le code OTP est invalide ou expiré'}, status=400)
