from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model
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
    
    CATEGORY_CHOICES = [
        ('CONF', 'Conférences'),
        ('WORK', 'Ateliers'),
        ('FEST', 'Festivals'),
        ('SPORT', 'Sport'),
        ('PARTY', 'Soirées'),
        ('EXPO', 'Expositions'),
        ('TRIP', 'Excursions'),
        ('CHAR', 'Événements caritatifs'),
        ('PROF', 'Rencontres professionnelles'),
        ('FAM', 'Famille et Enfants'),
    ]
    
    organizer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='private_events')
    interests = models.ManyToManyField('authentication.Interest', related_name='private_events', blank=True)
    participants = models.ManyToManyField(get_user_model(), related_name='participating_private_events', blank=True)
    category = models.CharField(max_length=5, choices=CATEGORY_CHOICES)

    def __str__(self):
        return f"{self.title} (Privé) - {self.get_category_display()}"


class EventRegistration(models.Model):
    """ Modèle pour les inscriptions aux événements """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey(PrivateEvent, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user} inscrit à {self.event}"


class Wishlist(models.Model):
    """ Modèle pour les listes de souhaits """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event = models.ForeignKey('PrivateEvent', on_delete=models.CASCADE, related_name='wishlists')

    def __str__(self):
        return f"Wishlist de {self.user} pour l'événement {self.event}"

