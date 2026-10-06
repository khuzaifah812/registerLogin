from django.contrib.auth.models import AbstractUser
from django.db import models


class Student(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    location = models.CharField(max_length=100, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    passport_photo = models.ImageField(upload_to='passports/', blank=True, null=True)
    academic_documents = models.FileField(upload_to='documents/', blank=True, null=True)
    email = models.EmailField(unique=True)
    is_student = models.BooleanField(default=True)
    
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username