from django.db import models

class EventBase(models.Model):
    """ Modèle de base abstrait pour les événements """
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    max_participants = models.IntegerField()

    class Meta:
        abstract = True

    def __str__(self):
        return f"{self.title} at {self.location} on {self.date} at {self.time}"


class PrivateEvent(EventBase):
    """ Modèle pour les événements particuliers """
    # Ici, on peut ajouter des champs spécifiques si besoin
    pass


class ProfessionalEvent(EventBase):
    """ Modèle pour les événements professionnels """
    price = models.DecimalField(max_digits=10, decimal_places=2)
    services = models.ManyToManyField('Service', related_name='professional_events')

    def __str__(self):
        return f"{self.title} (Professionnel)"


class Service(models.Model):
    """ Modèle pour les services associés aux événements professionnels """
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name
