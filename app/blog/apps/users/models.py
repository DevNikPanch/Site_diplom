from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField("ФИО", max_length=200, blank=True)
    phone_number = models.CharField("Номер телефона", max_length=20, blank=True)
    email = models.EmailField("Электронная почта", max_length=254, blank=True, null=True)

    def __str__(self):
        return f"Профиль: {self.user.username}"