# commissions/services.py
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import Commission
try:
    from mlm.models import MLMNode
except Exception:
    MLMNode = None

User = get_user_model()

DIRECT_RATE = getattr(settings, 'COMMISSION_DIRECT_RATE', 0.10)
BINARY_RATE = getattr(settings, 'COMMISSION_BINARY_RATE', 0.05)
AUTO_APPROVE = getattr(settings, 'AUTO_APPROVE_COMMISSIONS', False)


def create_commissions_for_sale(amount, telemarketer, sale_reference=None):
    """
    Shared logic to create commissions for a sale.
    - Direct commission to telemarketer
    - Optional binary match to upline (via MLMNode)
    - Optional auto-approve -> credits wallets
    """
    amount = Decimal(str(amount))
    created = []

    with transaction.atomic():
        # direct commission
        direct_amount = (Decimal(DIRECT_RATE) * amount).quantize(Decimal('0.01'))
        direct_comm = Commission.objects.create(
            telemarketer=telemarketer,
            amount=direct_amount,
            source='direct_sale',
            sale_reference=sale_reference,
        )
        created.append(direct_comm)

        # binary match
        if MLMNode:
            try:
                node = MLMNode.objects.get(user=telemarketer)
                parent = node.parent
                if parent and parent.user:
                    match_amount = (Decimal(BINARY_RATE) * amount).quantize(Decimal('0.01'))
                    match_comm = Commission.objects.create(
                        telemarketer=parent.user,
                        amount=match_amount,
                        source='binary_match',
                        sale_reference=sale_reference,
                    )
                    created.append(match_comm)
            except MLMNode.DoesNotExist:
                pass

        # auto-approve
        if AUTO_APPROVE and sale_reference:
            for comm in Commission.objects.filter(sale_reference=sale_reference):
                comm.approve(approver=None)

    return created
