import csv
import io
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from crm.models import Lead

User = get_user_model()

class Command(BaseCommand):
    help = "Import leads from CSV. Columns: name,email,phone,status,assigned_referral_code"

    def add_arguments(self, parser):
        parser.add_argument('csvfile', type=str)

    def handle(self, *args, **options):
        path = options['csvfile']
        created = 0
        with open(path, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader, start=1):
                name = row.get('name') or row.get('Name')
                if not name:
                    self.stdout.write(self.style.WARNING(f"Row {i}: missing name. Skipping."))
                    continue
                email = row.get('email', '')
                phone = row.get('phone', '')
                status = row.get('status', Lead.STATUS_CONTACTED)
                assigned_code = row.get('assigned_referral_code') or row.get('assigned_ref')
                assigned_to = None
                if assigned_code:
                    try:
                        assigned_to = User.objects.get(referral_code=assigned_code)
                    except User.DoesNotExist:
                        assigned_to = None
                Lead.objects.create(
                    name=name.strip(),
                    email=email.strip(),
                    phone=phone.strip(),
                    status=status if status in dict(Lead.STATUS_CHOICES) else Lead.STATUS_CONTACTED,
                    assigned_to=assigned_to
                )
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Imported {created} leads."))
