from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from PIL import Image

class EventBase(models.Model):
    """ Modèle de base abstrait pour les événements """
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    max_participants = models.IntegerField()
    image = models.ImageField(upload_to='event_images/', null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.title} at {self.location} on {self.date} at {self.time}"

class PrivateEvent(EventBase):
    """ Modèle pour les événements particuliers """
    interests = models.ManyToManyField('authentication.Interest', related_name='private_events', blank=True)

    def __str__(self):
        return f"{self.title} (Privé)"

class ProfessionalEvent(EventBase):
    """ Modèle pour les événements professionnels """
    price = models.DecimalField(max_digits=10, decimal_places=2)
    services = models.ManyToManyField('Service', related_name='professional_events')
    interests = models.ManyToManyField('authentication.Interest', related_name='professional_events', blank=True)

    def __str__(self):
        return f"{self.title} (Professionnel)"

class Service(models.Model):
    """ Modèle pour les services associés aux événements professionnels """
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

class EventRegistration(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('not_paid', 'Non payé'),
        ('pending', 'En attente'),
        ('paid', 'Payé'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Champs pour la relation générique vers PrivateEvent ou ProfessionalEvent
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    event = GenericForeignKey('content_type', 'object_id')

    registered_at = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='not_paid')

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')

    def __str__(self):
        return f"{self.user} inscrit à {self.event}"

class Wishlist(models.Model):
    """ Wishlist générique reliant à PrivateEvent ou ProfessionalEvent """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # Champs pour la relation générique vers PrivateEvent ou ProfessionalEvent
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    event = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"Wishlist de {self.user}"
