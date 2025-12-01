from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Wallet({self.user.username}) - {self.balance}"

    def credit(self, amount, note=None, commission=None):
        """
        Add a credit transaction and increase balance.
        """
        if amount <= 0:
            raise ValueError("credit amount must be positive")
        with transaction.atomic():
            WalletTransaction.objects.create(
                wallet=self,
                amount=amount,
                tx_type=WalletTransaction.TX_CREDIT,
                note=note or "Commission credit",
                related_commission=commission
            )
            self.balance = (self.balance or Decimal('0.00')) + Decimal(amount)
            self.save(update_fields=['balance'])

    def debit(self, amount, note=None):
        """
        Subtract amount from wallet and create debit transaction.
        """
        if amount <= 0:
            raise ValueError("debit amount must be positive")
        if (self.balance or Decimal('0.00')) < Decimal(amount):
            raise ValueError("insufficient balance")
        with transaction.atomic():
            WalletTransaction.objects.create(
                wallet=self,
                amount=amount,
                tx_type=WalletTransaction.TX_DEBIT,
                note=note or "Payout"
            )
            self.balance = self.balance - Decimal(amount)
            self.save(update_fields=['balance'])


class WalletTransaction(models.Model):
    TX_CREDIT = 'credit'
    TX_DEBIT = 'debit'
    TX_TYPES = [
        (TX_CREDIT, 'Credit'),
        (TX_DEBIT, 'Debit'),
    ]

    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    tx_type = models.CharField(max_length=10, choices=TX_TYPES)
    note = models.TextField(blank=True, null=True)
    related_commission = models.ForeignKey('Commission', null=True, blank=True, on_delete=models.SET_NULL, related_name='txs')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.wallet.user.username} {self.tx_type} {self.amount}"


class Commission(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_PAID = 'paid'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_PAID, 'Paid'),
    ]

    telemarketer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commissions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    source = models.CharField(max_length=255, blank=True, null=True)  # e.g. 'direct_sale', 'binary_match'
    sale_reference = models.CharField(max_length=255, blank=True, null=True, help_text="External sale/order id")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='approved_commissions')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sale_reference']),
            models.Index(fields=['telemarketer']),
        ]

    def __str__(self):
        return f"Commission({self.telemarketer.username}, {self.amount}, {self.status})"

    def approve(self, approver=None):
        """
        Mark commission as approved and credit wallet (transaction).
        Safe to call multiple times; idempotent.
        """
        if self.status == Commission.STATUS_APPROVED or self.status == Commission.STATUS_PAID:
            return  # already approved/paid

        # mark approved
        self.status = Commission.STATUS_APPROVED
        self.approved_at = timezone.now()
        if approver:
            self.approved_by = approver
        self.save(update_fields=['status', 'approved_at', 'approved_by'])

        # ensure wallet exists
        wallet, _ = Wallet.objects.get_or_create(user=self.telemarketer)
        wallet.credit(self.amount, note=f"Approved commission (sale {self.sale_reference})", commission=self)

    def mark_paid(self, approver=None):
        """
        Mark commission as paid (payout completed).
        """
        if self.status != Commission.STATUS_APPROVED:
            raise ValueError("Commission must be approved before marking as paid.")
        self.status = Commission.STATUS_PAID
        self.save(update_fields=['status'])
