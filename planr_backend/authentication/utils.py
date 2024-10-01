import random
from django.core.mail import send_mail
from django.conf import settings

def generate_otp(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

def send_email_otp(email, otp):
    send_mail(
        'Votre code de vérification',
        f'Votre code de vérification est : {otp}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    print(f"Code OTP envoyé à l'e-mail {email}: {otp}")

def send_sms_otp(phone_number, otp):
    # Simuler l'envoi d'un SMS en imprimant le code dans la console
    print(f"Code OTP envoyé au numéro {phone_number}: {otp}")
