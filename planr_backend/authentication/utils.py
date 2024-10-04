import random, bcrypt
from django.core.mail import send_mail
from django.conf import settings

def generate_otp():
    """
    Génère un OTP de 6 chiffres et retourne le hachage de l'OTP.

    Returns:
        tuple: OTP original et OTP haché.
    """
    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])  # Génération de l'OTP
    hashed_otp = bcrypt.hashpw(otp.encode('utf-8'), bcrypt.gensalt())  # Hachage de l'OTP avec bcrypt
    return otp, hashed_otp.decode('utf-8')  # Retourne l'OTP et son hachage

def send_email_otp(email, otp):
    """
    Envoie l'OTP par e-mail à l'utilisateur.

    Args:
        email (str): L'adresse e-mail de l'utilisateur.
        otp (str): Le code OTP à envoyer.
    """
    send_mail(
        'Votre code de vérification',
        f'Votre code de vérification est : {otp}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    print(f"Code OTP envoyé à l'e-mail {email}: {otp}")

def send_sms_otp(phone_number, otp):
    """
    Simule l'envoi d'un OTP par SMS.

    Args:
        phone_number (str): Le numéro de téléphone de l'utilisateur.
        otp (str): Le code OTP à envoyer.
    """
    print(f"Code OTP envoyé au numéro {phone_number}: {otp}")
