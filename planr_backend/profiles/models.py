from django.db import models
from django.conf import settings

class Profile(models.Model):
    ACCOUNT_TYPE_CHOICES = (
        ('personal', 'Particulier'),
        ('business', 'Entreprise'),
        ('premium', 'Premium'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    gender = models.CharField(max_length=10, choices=[('male', 'Homme'), ('female', 'Femme'), ('other', 'Autre')], null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    interests = models.ManyToManyField('Interest', blank=True)
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPE_CHOICES, default='personal')
    is_profile_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.first_name} - {self.account_type}"
    
    def check_profile_completion(self):
        required_fields = [self.first_name, self.birth_date, self.account_type]
        if all(required_fields) and self.interests.exists():
            self.is_profile_complete = True
        else:
            self.is_profile_complete = False
        self.save()

    def is_business(self):
        return self.account_type == 'business'

    def is_premium(self):
        return self.account_type == 'premium'

class Interest(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
