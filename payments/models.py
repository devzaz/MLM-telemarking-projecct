# payments/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

User = settings.AUTH_USER_MODEL

def default_now():
    return timezone.now()

def generate_request_id():
    # named function instead of lambda so migrations can be serialized
    return str(uuid.uuid4())

def payout_upload_to(instance, filename):
    # safe helper in case you later add a FileField that uses upload_to
    # prefer instance.user.id if you reference a ForeignKey named `user`
    uid = getattr(instance, "user_id", None) or getattr(getattr(instance, "user", None), "id", "unknown")
    return f"payouts/{uid}/{filename}"

class PayoutRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    ]

    # use a named callable for default (serializable)
    request_id = models.CharField(max_length=36, default=generate_request_id, unique=True)
    user = models.ForeignKey(User, related_name='payout_requests', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=8, default='BDT')   # change default if needed
    method = models.CharField(max_length=64, blank=True)  # e.g., 'bank_transfer', 'bKash', 'Rocket'
    details = models.JSONField(blank=True, null=True)  # e.g., bank account, phone number
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    admin_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=default_now)
    processed_at = models.DateTimeField(blank=True, null=True)
    processed_by = models.ForeignKey(User, related_name='processed_payouts', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        # avoid evaluating user heavy repr; use safe fallback
        user_repr = getattr(self.user, 'username', str(self.user))
        return f"Payout {self.request_id} ({user_repr}) - {self.amount} {self.currency}"
