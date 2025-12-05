from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid



class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('telemarketer', 'Telemarketer'),
        ('affiliate', 'Affiliate'),
        ('customer', 'Customer'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)


    # NEW FIELDS for email verification
    verification_token = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    verification_sent_at = models.DateTimeField(blank=True, null=True)


    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4())[:8].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"