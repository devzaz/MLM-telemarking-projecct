# reports/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

class Report(models.Model):
    """
    Saved report definition. `filters` is a simple JSON structure describing model, fields and operators.
    Example:
      {
        "model": "commissions.Commission",
        "filters": [
           {"field": "created_at", "op": "gte", "value": "2025-11-01"},
           {"field": "amount", "op": "gte", "value": 10}
        ],
        "name": "Big commissions",
        "owner_id": 1
      }
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    model = models.CharField(max_length=255)  # "app_label.ModelName"
    filters = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    schedule = models.CharField(max_length=32, blank=True, null=True)  # e.g. "daily", "weekly"

    def __str__(self):
        return self.name
    

    def latest_export(self):
        """Return the latest ReportExport or None."""
        # uses related_name='exports' defined on ReportExport.report FK
        return self.exports.order_by('-created_at').first()

class ReportExport(models.Model):
    """
    Tracks generated export CSVs.
    """
    STATUS_CHOICES = [
        ('queued','Queued'),
        ('running','Running'),
        ('done','Done'),
        ('error','Error'),
    ]
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='exports')
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='queued')
    file_path = models.CharField(max_length=1024, blank=True, null=True)
    error = models.TextField(blank=True, null=True)
    requested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def filename(self):
        return self.file_path.split('/')[-1] if self.file_path else None

    def __str__(self):
        return f"{self.report.name} export #{self.pk} ({self.status})"
