from django.core.management.base import BaseCommand
from payments.models import PayoutRequest
from django.contrib.auth import get_user_model
from payments.tasks import send_payout_notifications

User = get_user_model()

class Command(BaseCommand):
    help = "Create a test payout for user id=1 and run notification task sync"

    def handle(self, *args, **opts):
        u = User.objects.first()
        if not u:
            self.stdout.write("No users found")
            return
        pr = PayoutRequest.objects.create(user=u, amount=100.0, method='bkash', details={'phone': getattr(u,'phone','')})
        self.stdout.write(f"Created payout id={pr.pk}")
        # run task synchronously (for diagnostics)
        res = send_payout_notifications.apply(args=(pr.pk,'created'))
        self.stdout.write("Notification task executed")
