from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Lead

User = get_user_model()

class LeadModelTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='x', role='admin')
        self.tm = User.objects.create_user(username='tm', password='x', role='telemarketer')

    def test_create_lead(self):
        lead = Lead.objects.create(name='Test Lead', email='a@a.com', phone='12345', created_by=self.admin)
        self.assertEqual(Lead.objects.count(), 1)
        self.assertEqual(lead.status, Lead.STATUS_CONTACTED)

    def test_assign_lead(self):
        lead = Lead.objects.create(name='Assign Me', created_by=self.admin)
        lead.assigned_to = self.tm
        lead.save()
        self.assertEqual(lead.assigned_to.username, 'tm')
