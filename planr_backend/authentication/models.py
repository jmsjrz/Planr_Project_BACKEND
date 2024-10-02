from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta
import uuid
import hashlib

class UserManager(BaseUserManager):
    """
    Manager personnalisé pour le modèle User.
    """
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        """
        Crée un utilisateur avec un e-mail ou un numéro de téléphone.

        Args:
            email (str, optional): L'e-mail de l'utilisateur.
            phone_number (str, optional): Le numéro de téléphone de l'utilisateur.
            password (str, optional): Le mot de passe de l'utilisateur.
            extra_fields (dict): Champs supplémentaires.

        Returns:
            User: L'utilisateur créé.
        
        Raises:
            ValueError: Si ni l'e-mail ni le numéro de téléphone ne sont fournis.
        """
        if not email and not phone_number:
            raise ValueError('L\'utilisateur doit avoir un email ou un numéro de téléphone')
        
        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)  # Définit le mot de passe
        user.save(using=self._db)    # Sauvegarde l'utilisateur
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Crée un superutilisateur avec des privilèges d'administration.

        Args:
            email (str): L'e-mail de l'utilisateur.
            password (str, optional): Le mot de passe de l'utilisateur.
            extra_fields (dict): Champs supplémentaires.

        Returns:
            User: Le superutilisateur créé.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(email=email, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Modèle d'utilisateur personnalisé.
    """
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    otp = models.CharField(max_length=64, null=True, blank=True)  # Champ pour stocker l'OTP haché
    otp_created_at = models.DateTimeField(null=True, blank=True)  # Champ pour la date de création de l'OTP
    reset_token = models.CharField(max_length=64, null=True, blank=True)  # Champ pour le token de réinitialisation
    reset_token_expiration = models.DateTimeField(null=True, blank=True)  # Expiration du token de réinitialisation
    failed_login_attempts = models.IntegerField(default=0)  # Nombre de tentatives de connexion échouées
    failed_otp_attempts = models.IntegerField(default=0)  # Nombre de tentatives d'OTP échouées
    locked_until = models.DateTimeField(null=True, blank=True)  # Date/heure jusqu'à laquelle le compte est verrouillé
    is_active = models.BooleanField(default=True)  # Indique si le compte est actif
    is_staff = models.BooleanField(default=False)  # Indique si l'utilisateur peut accéder à l'admin

    objects = UserManager()  # Associe le manager personnalisé

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email if self.email else self.phone_number

    def is_otp_valid(self, otp):
        """
        Vérifie si le code OTP est valide (correspondant et non expiré).

        Args:
            otp (str): Le code OTP soumis par l'utilisateur.

        Returns:
            bool: True si le code OTP est valide, False sinon.
        """
        if self.otp and self.otp_created_at:
            expiration_time = self.otp_created_at + timedelta(minutes=10)  # L'OTP est valide pendant 10 minutes
            hashed_otp = hashlib.sha256(otp.encode()).hexdigest()  # Hachage de l'OTP soumis
            return hashed_otp == self.otp and timezone.now() <= expiration_time
        return False

    def generate_reset_token(self):
        """
        Génère un token de réinitialisation et définit sa date d'expiration.
        """
        self.reset_token = str(uuid.uuid4())  # Génère un identifiant unique
        self.reset_token_expiration = timezone.now() + timedelta(hours=1)  # Le token est valide pendant 1 heure
        self.save()
        
    def is_reset_token_valid(self, token):
        """
        Vérifie si le token de réinitialisation est valide (correspondant et non expiré).

        Args:
            token (str): Le token de réinitialisation.

        Returns:
            bool: True si le token est valide, False sinon.
        """
        return self.reset_token == token and self.reset_token_expiration and timezone.now() <= self.reset_token_expiration
    
    def lock_account(self, minutes=10):
        """
        Verrouille le compte de l'utilisateur pour une durée déterminée.

        Args:
            minutes (int, optional): Le nombre de minutes pendant lesquelles le compte doit être verrouillé. 
                                     La valeur par défaut est 10 minutes.
        """
        self.locked_until = timezone.now() + timedelta(minutes=minutes)
        self.save()

    def is_account_locked(self):
        """
        Vérifie si le compte de l'utilisateur est actuellement verrouillé.

        Returns:
            bool: True si le compte est verrouillé, False sinon.
        """
        if self.locked_until and timezone.now() < self.locked_until:
            return True
        return False
    
class PasswordResetAttempt(models.Model):
    """
    Modèle pour suivre les tentatives de réinitialisation de mot de passe d'un utilisateur.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reset_attempts')
    requested_at = models.DateTimeField(auto_now_add=True)  # Date/heure de la tentative de réinitialisation
    ip_address = models.CharField(max_length=45, null=True, blank=True)  # Adresse IP de la demande
    user_agent = models.CharField(max_length=256, null=True, blank=True)  # User agent du navigateur

    def __str__(self):
        return f"Tentative de réinitialisation de {self.user.email if self.user.email else self.user.phone_number} à {self.requested_at}"
