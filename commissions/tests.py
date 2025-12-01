from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.urls import reverse
from .models import Commission, Wallet, WalletTransaction
from django.conf import settings

User = get_user_model()

class CommissionFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(username='staff', password='pass', is_staff=True)
        self.tele = User.objects.create_user(username='tele', password='pass')
        # ensure wallet exists
        Wallet.objects.create(user=self.tele)

    def test_api_record_sale_creates_commission(self):
        url = reverse('commissions:api_record_sale')
        resp = self.client.post(url, data={'amount': '100.00', 'telemarketer_id': self.tele.id, 'sale_reference': 'TST-1'}, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(Commission.objects.filter(sale_reference='TST-1').exists())

    def test_admin_approve_action_credits_wallet(self):
        # create commission pending
        comm = Commission.objects.create(telemarketer=self.tele, amount=Decimal('10.00'), source='direct_sale')
        self.assertEqual(comm.status, Commission.STATUS_PENDING)
        # call approve method
        comm.approve(approver=self.staff)
        comm.refresh_from_db()
        self.assertEqual(comm.status, Commission.STATUS_APPROVED)
        wallet = Wallet.objects.get(user=self.tele)
        # transaction created and balance updated
        self.assertTrue(WalletTransaction.objects.filter(wallet=wallet, related_commission=comm).exists())
        self.assertEqual(wallet.balance, Decimal('10.00'))
