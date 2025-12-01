from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import ReferralToken, ReferralConversion
import json
User = get_user_model()

@override_settings(REFERRAL_SHARED_SECRET='TESTSECRET')
class ReferralFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.referrer = User.objects.create_user(
            username='ref',
            password='x',
            referral_code='REFCODE1'
        )

    def test_middleware_sets_cookie_and_token(self):
        resp = self.client.get('/?ref=REFCODE1')
        cookie = resp.cookies.get('referral_token')
        self.assertIsNotNone(cookie)
        token = ReferralToken.objects.get(code=cookie.value)
        self.assertEqual(token.referrer.username, 'ref')

    def test_api_record_conversion_with_shared_secret(self):
        token = ReferralToken.objects.create(referrer=self.referrer)

        url = reverse('referrals:api_record_conversion')

        resp = self.client.post(
            url,
            data=json.dumps({
                'token': token.code,
                'external_order_id': 'ORD123',
                'amount': '99.90'
            }),
            content_type='application/json',
            HTTP_X_REF_SHARED_SECRET='TESTSECRET'
        )

        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(ReferralConversion.objects.count(), 1)
