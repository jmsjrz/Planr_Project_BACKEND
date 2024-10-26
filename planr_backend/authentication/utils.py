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


def send_email(subject, message, recipient_list):
    """
    Envoie un e-mail à l'utilisateur.

    Args:
        subject (str): Le sujet de l'e-mail.
        message (str): Le contenu de l'e-mail.
        recipient_list (list): Liste des destinataires.
    """
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        logger.info(f"E-mail envoyé à {', '.join(recipient_list)}")
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'e-mail à {', '.join(recipient_list)}: {e}")


def send_email_otp(email, otp):
    """
    Envoie un code OTP par e-mail à l'utilisateur.

    Args:
        email (str): L'adresse e-mail de l'utilisateur.
        otp (str): Le code OTP à envoyer.
    """
    send_email('Votre code de vérification', f'Votre code de vérification est : {otp}', [email])


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
    message = f"Une nouvelle connexion a été effectuée sur votre compte depuis l'adresse IP {ip_address} et l'appareil {user_agent}."
    send_email('Nouvelle connexion détectée', message, [email])
