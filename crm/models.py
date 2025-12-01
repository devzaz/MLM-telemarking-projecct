from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class Lead(models.Model):
    STATUS_CONTACTED = 'contacted'
    STATUS_FOLLOW_UP = 'follow_up'
    STATUS_CONVERTED = 'converted'
    STATUS_LOST = 'lost'

    STATUS_CHOICES = [
        (STATUS_CONTACTED, 'Contacted'),
        (STATUS_FOLLOW_UP, 'Follow-up'),
        (STATUS_CONVERTED, 'Converted'),
        (STATUS_LOST, 'Lost'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_CONTACTED)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='leads')
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_leads')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f"{self.name} ({self.email or self.phone or 'no contact'})"

class LeadNote(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='lead_notes')
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Lead Note'
        verbose_name_plural = 'Lead Notes'

    def __str__(self):
        return f"Note for {self.lead_id} by {self.author or 'system'}"
