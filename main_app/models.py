from django.db import models
from django.contrib.auth.models import User


class Image(models.Model):
    image = models.ImageField(default="")

    def __str__(self):
        return str(self.image)


class TypeEntreprise(models.Model):
    types = (('publique', 'publique'), ('prive', 'prive'))
    type = models.CharField(max_length=255, choices=types)


class Entreprise(models.Model):
    secteurs = (('Publique', 'Publique'), ('Prive', 'Privé'))
    nom = models.CharField(max_length=300, null=False, blank=False)
    activite = models.CharField(max_length=255, null=False, blank=False)
    secteurActivite = models.CharField(choices=secteurs, null=False, blank=False, max_length=255)
    capitale = models.DecimalField(null=False, blank=False, decimal_places=2, max_digits=10)
    pays = models.CharField(max_length=255, blank=False, null=False)
    ville = models.CharField(max_length=255, null=False, blank=False)
    codePostal = models.IntegerField()
    telephone = models.DecimalField(max_digits=10, decimal_places=2)
    siteInternet = models.CharField(max_length=300)
    typeEntreprise = models.ForeignKey(TypeEntreprise, on_delete=models.CASCADE)


class Profil(models.Model):
    user = models.OneToOneField(User, blank=True, null=True, on_delete=models.CASCADE)
    token_email = models.CharField(max_length=300, blank=True, null=True, default="")
    token_email_expiration = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.user.username

class Contact(models.Model):
    full_name = models.CharField( max_length=300)
    email = models.EmailField()
    message = models.TextField()
    
    def __str__(self):
        return self.full_name
