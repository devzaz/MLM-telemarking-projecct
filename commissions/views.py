from decimal import Decimal
from django.conf import settings
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist

from .models import Commission, Wallet, WalletTransaction
User = get_user_model()

# Attempt to import MLMNode for binary placement (if available)
try:
    from mlm.models import MLMNode
except Exception:
    MLMNode = None

# settings defaults
DIRECT_RATE = getattr(settings, 'COMMISSION_DIRECT_RATE', 0.10)  # 10% default
BINARY_RATE = getattr(settings, 'COMMISSION_BINARY_RATE', 0.05)  # 5% up-line matching
AUTO_APPROVE = getattr(settings, 'AUTO_APPROVE_COMMISSIONS', False)


@api_view(['POST'])
@permission_classes([AllowAny])  # If you want authentication, change accordingly
def api_record_sale(request):
    """
    Record a sale and calculate commissions.
    Body JSON:
    {
      "amount": 99.99,
      "telemarketer_id": 12,
      "sale_reference": "ORDER-123",
      "buyer_id": 45   # optional
    }

    Response: created commissions
    """
    data = request.data
    try:
        amount = Decimal(str(data.get('amount')))
        tele_id = int(data.get('telemarketer_id'))
    except Exception:
        return Response({"detail": "Invalid payload: amount and telemarketer_id required."}, status=status.HTTP_400_BAD_REQUEST)

    sale_reference = data.get('sale_reference')
    buyer_id = data.get('buyer_id')

    # prevent double processing by sale_reference if provided
    if sale_reference:
        if Commission.objects.filter(sale_reference=sale_reference).exists():
            return Response({"detail": "Sale already processed"}, status=status.HTTP_409_CONFLICT)

    # get telemarketer user
    try:
        tele = User.objects.get(pk=tele_id)
    except User.DoesNotExist:
        return Response({"detail": "Telemarketer not found"}, status=status.HTTP_404_NOT_FOUND)

    created = []
    with transaction.atomic():
        # calculate direct commission
        direct_amount = (Decimal(DIRECT_RATE) * amount).quantize(Decimal('0.01'))
        direct_comm = Commission.objects.create(
            telemarketer=tele,
            amount=direct_amount,
            source='direct_sale',
            sale_reference=sale_reference
        )
        created.append({'id': direct_comm.id, 'telemarketer': tele.id, 'amount': str(direct_comm.amount), 'source': direct_comm.source})

        # binary matching: if mlm is present and tele has a node with parent, give matching to parent
        if MLMNode:
            try:
                node = MLMNode.objects.get(user=tele)
                parent = node.parent
                if parent and parent.user:
                    # matching commission to upline telemarketer if they exist
                    match_amount = (Decimal(BINARY_RATE) * amount).quantize(Decimal('0.01'))
                    match_comm = Commission.objects.create(
                        telemarketer=parent.user,
                        amount=match_amount,
                        source='binary_match',
                        sale_reference=sale_reference
                    )
                    created.append({'id': match_comm.id, 'telemarketer': parent.user.id, 'amount': str(match_comm.amount), 'source': match_comm.source})
            except MLMNode.DoesNotExist:
                pass

        # auto-approve if configured
        if AUTO_APPROVE:
            for comm_id in Commission.objects.filter(sale_reference=sale_reference).values_list('id', flat=True):
                comm = Commission.objects.get(pk=comm_id)
                comm.approve(approver=None)

    return Response({'created': created}, status=status.HTTP_201_CREATED)


# ----- Frontend views: wallet summary + commission history -----
@staff_member_required
def wallet_summary_view(request):
    """
    Staff view showing overall wallet KPIs and mini chart.
    """
    from django.utils import timezone
    now = timezone.now()
    wallets = Wallet.objects.select_related('user').all()
    total_balance = sum([w.balance or Decimal('0.00') for w in wallets])
    total_commissions = Commission.objects.count()
    pending = Commission.objects.filter(status=Commission.STATUS_PENDING).count()
    approved = Commission.objects.filter(status=Commission.STATUS_APPROVED).count()

    # simple data for mini chart: approvals last 14 days
    days = []
    counts = []
    for i in range(13, -1, -1):
        day = (now - timezone.timedelta(days=i)).date()
        days.append(day.strftime('%b %d'))
        counts.append(Commission.objects.filter(approved_at__date=day).count())

    context = {
        'total_balance': total_balance,
        'total_commissions': total_commissions,
        'pending': pending,
        'approved': approved,
        'chart_labels': days,
        'chart_data': counts,
    }
    return render(request, 'commissions/wallet_summary.html', context)


def commission_history_view(request):
    """
    Commission history page:
    - Staff: shows all commissions.
    - Telemarketer: shows only their commissions.
    """
    from django.core.paginator import Paginator
    user = request.user
    qs = Commission.objects.select_related('telemarketer', 'approved_by').order_by('-created_at')
    if not user.is_staff:
        # show telemarketer's own commissions
        qs = qs.filter(telemarketer=user)

    paginator = Paginator(qs, 20)
    page_num = request.GET.get('page', 1)
    page = paginator.get_page(page_num)
    return render(request, 'commissions/commission_history.html', {'page': page})
