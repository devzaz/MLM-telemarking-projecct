# reports/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Report

User = get_user_model()

class ReportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='t1', password='pw', role='telemarketer')

    def test_create_report(self):
        self.client.login(username='t1', password='pw')
        resp = self.client.post('/api/reports/reports/', {'name':'My test','filters':{}}, content_type='application/json')
        self.assertIn(resp.status_code, (200,201,201))
