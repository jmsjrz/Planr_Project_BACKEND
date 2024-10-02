import random, hashlib
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    """
    Génère un OTP de 6 chiffres et retourne le hachage de l'OTP.
    
    Returns:
        tuple: OTP original et OTP haché.
    """
    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])  # Génère un OTP de 6 chiffres
    hashed_otp = hashlib.sha256(otp.encode()).hexdigest()  # Hachage de l'OTP
    return otp, hashed_otp  # Retourne l'OTP original et le haché

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
