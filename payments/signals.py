# payments/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PayoutRequest
from notifications.models import Notification
from django.urls import reverse

@receiver(post_save, sender=PayoutRequest)
def payout_post_save(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(user=instance.user, title="Payout submitted", message=f"Your payout request {instance.request_id} is submitted.", url=reverse('payments:detail', args=[instance.pk]))
