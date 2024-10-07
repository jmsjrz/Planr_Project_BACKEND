import random
import hashlib
from django.core.mail import send_mail
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def generate_and_hash_otp():
    """
    Génère un OTP de 6 chiffres et retourne le hachage de l'OTP.

    Returns:
        tuple: OTP original et OTP haché.
    """
    otp = '123456' if settings.DEBUG else ''.join([str(random.randint(0, 9)) for _ in range(6)])  # OTP fixe si DEBUG
    hashed_otp = hashlib.sha256(otp.encode('utf-8')).hexdigest()  # Hachage de l'OTP avec SHA256
    return otp, hashed_otp

def send_email_otp(email, otp):
    """
    Envoie un code OTP par e-mail à l'utilisateur.

    Args:
        email (str): L'adresse e-mail de l'utilisateur.
        otp (str): Le code OTP à envoyer.
    """
    try:
        send_mail(
            'Votre code de vérification',
            f'Votre code de vérification est : {otp}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f"Code OTP envoyé à l'e-mail {email}")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du code OTP à {email}: {e}")

def send_sms_otp(phone_number, otp):
    """
    Simule l'envoi d'un OTP par SMS à l'utilisateur.

    Args:
        phone_number (str): Le numéro de téléphone de l'utilisateur.
        otp (str): Le code OTP à envoyer.
    """
    # Simuler l'envoi d'un SMS. En production, intégrer un service comme Twilio ou Nexmo
    logger.info(f"Code OTP envoyé au numéro {phone_number}: {otp}")

def send_login_alert(email, ip_address, user_agent):
    """
    Envoie une alerte par e-mail à l'utilisateur lors d'une nouvelle connexion détectée.

    Args:
        email (str): L'adresse e-mail de l'utilisateur.
        ip_address (str): L'adresse IP utilisée lors de la connexion.
        user_agent (str): Le user agent de l'appareil utilisé lors de la connexion.
    """
    try:
        send_mail(
            'Nouvelle connexion détectée',
            f'Une nouvelle connexion a été effectuée sur votre compte depuis l\'adresse IP {ip_address} et l\'appareil {user_agent}.',
            'no-reply@planr.dev',
            [email],
        )
        logger.info(f"Alerte de connexion envoyée à l'e-mail {email}")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'alerte de connexion à {email}: {e}")
