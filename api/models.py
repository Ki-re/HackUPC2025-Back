from django.db import models

class Party(models.Model):
    code = models.CharField(max_length=8, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

class User(models.Model):
    party = models.ForeignKey(Party, related_name='members', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    budget = models.DecimalField(max_digits=8, decimal_places=2)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Preference(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='preferences')
    green_travel = models.BooleanField(default=False)
    culture = models.IntegerField(default=0)
    food = models.IntegerField(default=0)
    outdoors = models.IntegerField(default=0)
    weather = models.IntegerField(default=0)
    events = models.IntegerField(default=0)

    def __str__(self):
        return f"Preferencias de {self.user.name}"
    
class Vote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    destination = models.CharField(max_length=100)
    vote = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)

class SuggestedDestination(models.Model):
    party = models.ForeignKey(Party, related_name='suggested_destinations', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    image_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
class Informacion(models.Model):
    party = models.OneToOneField('Party', on_delete=models.CASCADE)
    pais_recomendado = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.party.name} → {self.pais_recomendado}"
