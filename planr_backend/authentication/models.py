from django.db import models

# Create your models here.
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from datetime import timedelta

class UserManager(BaseUserManager):
    def create_user(self, email=None, phone_number=None, password=None, **extra_fields):
        if not email and not phone_number:
            raise ValueError('L\'utilisateur doit avoir un email ou un numéro de téléphone')
        
        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        return self.create_user(email=email, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    otp = models.CharField(max_length=6, null=True, blank=True)  # Champ pour stocker l'OTP
    otp_created_at = models.DateTimeField(null=True, blank=True)  # Champ pour la date de création de l'OTP
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
            otp (str): Le code OTP soumis par l'utilisateur.

        Returns:
            bool: True si le code OTP est valide, False sinon.
        """
        if self.otp == otp and self.otp_created_at:
            expiration_time = self.otp_created_at + timedelta(minutes=10)  # L'OTP est valide pendant 10 minutes
            return timezone.now() <= expiration_time
        return False
