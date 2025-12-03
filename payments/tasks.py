# payments/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import PayoutRequest
from notifications.models import Notification
import logging
logger = logging.getLogger(__name__)

@shared_task
def send_payout_notifications(payout_pk, event='created'):
    try:
        pr = PayoutRequest.objects.select_related('user').get(pk=payout_pk)
    except PayoutRequest.DoesNotExist:
        logger.error("PayoutRequest %s not found", payout_pk)
        return

    user = pr.user
    # messages for user
    mapping = {
        'created': (f'Payout request received', f'Your payout request {pr.request_id} for {pr.amount} is received and pending.'),
        'approved': (f'Payout approved', f'Your payout request {pr.request_id} for {pr.amount} was approved.'),
        'rejected': (f'Payout rejected', f'Your payout request {pr.request_id} for {pr.amount} was rejected.'),
        'paid': (f'Payout paid', f'Your payout request {pr.request_id} for {pr.amount} has been marked as paid.'),
    }
    title, body = mapping.get(event, mapping['created'])
    # create DB notification
    Notification.objects.create(user=user, title=title, message=body, url=f'/payments/detail/{pr.pk}/')

    # send email if enabled
    if getattr(settings, 'NOTIFICATIONS_SEND_EMAIL', True):
        try:
            send_mail(subject=title, message=body, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[user.email], fail_silently=False)
        except Exception as e:
            logger.exception("Failed to send payout email %s: %s", pr.pk, e)

    # optionally send SMS via Twilio if configured
    if getattr(settings, 'NOTIFICATIONS_SEND_SMS', False):
        try:
            from twilio.rest import Client
            sid = settings.TWILIO_ACCOUNT_SID
            token = settings.TWILIO_AUTH_TOKEN
            from_num = settings.TWILIO_FROM_NUMBER
            client = Client(sid, token)
            phone = None
            # try to fetch phone number from pr.details
            if pr.details and isinstance(pr.details, dict):
                phone = pr.details.get('phone') or pr.details.get('mobile')
            if not phone and hasattr(user, 'phone'):
                phone = getattr(user, 'phone')
            if phone:
                client.messages.create(body=body, from_=from_num, to=str(phone))
        except Exception as e:
            logger.exception("Failed sending twilio SMS for payout %s: %s", pr.pk, e)
