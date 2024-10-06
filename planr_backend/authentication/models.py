from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid
import hashlib


class UserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle User. Permet de créer des utilisateurs et des superutilisateurs.
    """
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        """
        Crée un utilisateur avec un e-mail ou un numéro de téléphone.

        Args:
            email (str): L'adresse e-mail de l'utilisateur.
            phone_number (str): Le numéro de téléphone de l'utilisateur.
            password (str): Le mot de passe de l'utilisateur.

        Returns:
            User: L'utilisateur créé.
        """
        if not email and not phone_number:
            raise ValueError("L'utilisateur doit avoir un email ou un numéro de téléphone")

        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crée un superutilisateur avec des privilèges d'administration.

        Args:
            email (str): L'adresse e-mail du superutilisateur.
            password (str): Le mot de passe du superutilisateur.

        Returns:
            User: Le superutilisateur créé.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')

        return self.create_user(email=email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle d'utilisateur personnalisé.
    """
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    otp = models.CharField(max_length=128, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    reset_token = models.CharField(max_length=128, null=True, blank=True)
    reset_token_expiration = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.CharField(max_length=45, null=True, blank=True)
    last_login_user_agent = models.CharField(max_length=256, null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    failed_otp_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email if self.email else self.phone_number

    def is_otp_valid(self, otp):
        """
        Vérifie si le code OTP est valide (correspondant et non expiré).

        Args:
            otp (str): Le code OTP à vérifier.

        Returns:
            bool: True si le code OTP est valide, sinon False.
        """
        if self.otp and self.otp_created_at:
            expiration_time = self.otp_created_at + timedelta(minutes=10)
            otp_hash = hashlib.sha256(otp.encode('utf-8')).hexdigest()
            return otp_hash == self.otp and timezone.now() <= expiration_time
        return False

    def generate_reset_token(self):
        """
        Génère un token de réinitialisation et définit sa date d'expiration.
        """
        self.reset_token = str(uuid.uuid4())
        self.reset_token_expiration = timezone.now() + timedelta(hours=1)
        self.save()

    def is_reset_token_valid(self, token):
        """
        Vérifie si le token de réinitialisation est valide (correspondant et non expiré).

        Args:
            token (str): Le token à vérifier.

        Returns:
            bool: True si le token est valide, sinon False.
        """
        return self.reset_token == token and self.reset_token_expiration and timezone.now() <= self.reset_token_expiration

    def lock_account(self, minutes=10):
        """
        Verrouille le compte de l'utilisateur pour une durée déterminée.

        Args:
            minutes (int): Durée du verrouillage en minutes.
        """
        self.locked_until = timezone.now() + timedelta(minutes=minutes)
        self.save()

    def is_account_locked(self):
        """
        Vérifie si le compte de l'utilisateur est actuellement verrouillé.

        Returns:
            bool: True si le compte est verrouillé, sinon False.
        """
        return self.locked_until and timezone.now() < self.locked_until


class PasswordResetAttempt(models.Model):
    """
    Modèle pour suivre les tentatives de réinitialisation de mot de passe d'un utilisateur.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_attempts')
    requested_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    user_agent = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return f"Tentative de réinitialisation de {self.user.email if self.user.email else self.user.phone_number} à {self.requested_at}"
