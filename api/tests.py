# api/tests.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from referrals.models import ReferralToken

User = get_user_model()

class ApiIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='svc', password='pass1234')
        self.client = APIClient()
        # obtain JWT token
        resp = self.client.post('/api/token/', {'username': 'svc', 'password': 'pass1234'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.token = resp.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_referral_check_and_sale_verify(self):
        # create referral token
        ref = ReferralToken.objects.create(code='TESTREF', active=True, expires_at=None, referrer=self.user)
        # check referral
        resp = self.client.post('/api/referral/check/', {'token': 'TESTREF'}, format='json')
        self.assertEqual(resp.status_code, 200)
        # verify sale
        payload = {
            'external_order_id': 'EXT-1',
            'amount': '10.00',
            'referral_token': 'TESTREF'
        }
        resp = self.client.post('/api/sale/verify/', payload, format='json')
        self.assertIn(resp.status_code, (200, 201))
