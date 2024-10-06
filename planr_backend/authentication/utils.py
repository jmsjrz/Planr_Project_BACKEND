import random
import hashlib
from django.conf import settings


def generate_otp():
    """
    Génère un OTP de 6 chiffres et retourne le hachage de l'OTP.

    Returns:
        tuple: OTP original et OTP haché.
    """
    otp = '123456' if settings.DEBUG else ''.join([str(random.randint(0, 9)) for _ in range(6)])  # OTP fixe si DEBUG
    hashed_otp = hashlib.sha256(otp.encode('utf-8')).hexdigest()  # Hachage de l'OTP avec SHA256
    return otp, hashed_otp
