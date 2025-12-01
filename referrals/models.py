
from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid
from datetime import timedelta
import secrets

User = settings.AUTH_USER_MODEL

def default_expiry_days():
    return getattr(settings, 'REFERRAL_COOKIE_AGE_DAYS', 180)

class ReferralToken(models.Model):
    """
    A token representing a tracked referral. Created when a visitor arrives with a
    referral code (or when we create an on-behalf token). Token.code is what we place
    in a cookie on the visitor's browser.
    """
    code = models.CharField(max_length=64, unique=True, db_index=True)
    referrer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_tokens')
    source_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = uuid.uuid4().hex
        if not self.expires_at:
            days = default_expiry_days()
            self.expires_at = timezone.now() + timedelta(days=days)
        super().save(*args, **kwargs)

    def is_expired(self):
        return self.expires_at <= timezone.now()

    def __str__(self):
        return f"{self.referrer} -> {self.code[:8]} ({'expired' if self.is_expired() else 'active'})"


class ReferralConversion(models.Model):
    """
    Record a purchase (or conversion event) that originated from a referral token.
    Connected sites should call the API with the token code or referral_code and order details.
    """
    referral_token = models.ForeignKey(ReferralToken, null=True, blank=True, on_delete=models.SET_NULL, related_name='conversions')
    referrer = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='referral_conversions')
    external_order_id = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['external_order_id']),
        ]

    def __str__(self):
        return f"Conversion {self.external_order_id or self.pk} for {self.referrer}"
    






class ApiServiceKey(models.Model):
    """
    Simple API service key model (for partner/service accounts).
    Partner calls should provide header: Authorization: Token <key>
    """
    name = models.CharField(max_length=120, help_text="Name for this key (partner name)")
    key = models.CharField(max_length=64, unique=True, db_index=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                             help_text="Optional link to a User (service owner)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, default="")

    def save(self, *args, **kwargs):
        if not self.key:
            # generate a secure token
            self.key = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'disabled'})"