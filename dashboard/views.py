from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from referrals.models import ReferralToken, ReferralConversion
from django.utils import timezone

# @login_required
# def index(request):
#     user = request.user
#     if not user.is_verified or not user.is_approved:
#         return render(request, 'dashboard/pending.html')
    

#     active = ReferralToken.objects.filter(active=True, expires_at__gt=timezone.now()).count()
#     total_conv = ReferralConversion.objects.count()
#     conversion_rate = (total_conv / active) if active else 0
#     return render(request, 'dashboard/index.html', {'user': user,'active_referrals': active, 'total_conversions': total_conv, 'conversion_rate': conversion_rate})




# dashboard/views.py
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)

# @login_required
# def index(request):
#     """
#     Renders the dashboard page. The page fetches JSON via API endpoints below.
#     """
#     return render(request, 'dashboard/index.html', {})


@login_required
def index(request):
    user = request.user
    if not user.is_verified or not user.is_approved:
        return render(request, 'dashboard/pending.html')
    

    active = ReferralToken.objects.filter(active=True, expires_at__gt=timezone.now()).count()
    total_conv = ReferralConversion.objects.count()
    conversion_rate = (total_conv / active) if active else 0
    return render(request, 'dashboard/test_index.html', {'user': user,'active_referrals': active, 'total_conversions': total_conv, 'conversion_rate': conversion_rate})




# ---------- API endpoints (DRF) ----------
class DashboardSummaryAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """
        Return summary numbers used by the admin dashboard:
         - total_users
         - total_leads, converted_leads_last_30d
         - total_sales, total_commissions (if commissions app exists)
         - referrals_active (if referrals app exists)
         - new_users_last_30d
        """
        now = timezone.now()
        last_30 = now - timedelta(days=30)
        data = {}
        # Users
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            data['total_users'] = User.objects.count()
            data['new_users_last_30'] = User.objects.filter(date_joined__gte=last_30).count()
        except Exception as e:
            logger.warning("Users model unavailable: %s", e)
            data['total_users'] = None
            data['new_users_last_30'] = None

        # CRM / Leads
        try:
            from crm.models import Lead
            data['total_leads'] = Lead.objects.count()
            data['converted_leads'] = Lead.objects.filter(status__iexact='Converted').count()
            data['converted_last_30'] = Lead.objects.filter(status__iexact='Converted', updated_at__gte=last_30).count()
            # leads per status
            status_counts = list(Lead.objects.values('status').annotate(count=Count('pk')))
            data['lead_status_counts'] = status_counts
        except Exception as e:
            logger.warning("Lead model unavailable: %s", e)
            data.update({
                'total_leads': None,
                'converted_leads': None,
                'converted_last_30': None,
                'lead_status_counts': [],
            })

        # Commissions / Sales
        try:
            from commissions.models import Commission
            total_commissions = Commission.objects.aggregate(total=Sum('amount'))['total'] or 0
            total_paid = Commission.objects.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
            data['total_commissions'] = float(total_commissions)
            data['total_commissions_paid'] = float(total_paid)
            data['commissions_last_30'] = float(Commission.objects.filter(created_at__gte=last_30).aggregate(total=Sum('amount'))['total'] or 0)
        except Exception as e:
            logger.warning("Commission model unavailable: %s", e)
            data.update({
                'total_commissions': None,
                'total_commissions_paid': None,
                'commissions_last_30': None,
            })

        # Referrals
        try:
            from referrals.models import ReferralConversion
            data['referrals_total'] = ReferralConversion.objects.count()
            data['referrals_last_30'] = ReferralConversion.objects.filter(created_at__gte=last_30).count()
        except Exception as e:
            logger.warning("Referral model unavailable: %s", e)
            data.update({'referrals_total': None, 'referrals_last_30': None})

        # Simple monthly trend example (last 6 days) for chart
        try:
            days = []
            counts = []
            for i in range(6, -1, -1):
                d = now - timedelta(days=i)
                start = d.replace(hour=0, minute=0, second=0, microsecond=0)
                end = start + timedelta(days=1)
                cnt = 0
                if 'total_leads' in data and data['total_leads'] is not None:
                    cnt = Lead.objects.filter(created_at__gte=start, created_at__lt=end).count()
                days.append(start.strftime('%Y-%m-%d'))
                counts.append(cnt)
            data['lead_trend_days'] = days
            data['lead_trend_counts'] = counts
        except Exception as e:
            data['lead_trend_days'] = []
            data['lead_trend_counts'] = []

        return Response(data)


class TelemarketerOverviewAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_id, *args, **kwargs):
        """
        Returns simple numbers for a telemarketer:
         - leads_assigned
         - leads_converted
         - earnings (if commissions)
        """
        data = {}
        try:
            from crm.models import Lead
            leads_assigned = Lead.objects.filter(telemarketer_id=user_id).count()
            converted = Lead.objects.filter(telemarketer_id=user_id, status__iexact='Converted').count()
            data['leads_assigned'] = leads_assigned
            data['leads_converted'] = converted
        except Exception as e:
            logger.warning("telemarketer overview: lead model missing %s", e)
            data['leads_assigned'] = None
            data['leads_converted'] = None

        try:
            from commissions.models import Commission
            sum_comm = Commission.objects.filter(telemarketer_id=user_id).aggregate(total=Sum('amount'))['total'] or 0
            data['commissions_total'] = float(sum_comm)
        except Exception as e:
            data['commissions_total'] = None

        return Response(data)

    permission_classes = (IsAuthenticated,)

    def get(self, request, user_id, *args, **kwargs):
        """
        Returns simple numbers for a telemarketer:
         - leads_assigned
         - leads_converted
         - earnings (if commissions)
        """
        data = {}
        try:
            from crm.models import Lead
            leads_assigned = Lead.objects.filter(telemarketer_id=user_id).count()
            converted = Lead.objects.filter(telemarketer_id=user_id, status__iexact='Converted').count()
            data['leads_assigned'] = leads_assigned
            data['leads_converted'] = converted
        except Exception as e:
            logger.warning("telemarketer overview: lead model missing %s", e)
            data['leads_assigned'] = None
            data['leads_converted'] = None

        try:
            from commissions.models import Commission
            sum_comm = Commission.objects.filter(telemarketer_id=user_id).aggregate(total=Sum('amount'))['total'] or 0
            data['commissions_total'] = float(sum_comm)
        except Exception as e:
            data['commissions_total'] = None

        return Response(data)

