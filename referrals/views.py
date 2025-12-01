from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from decimal import Decimal
import json

from .models import ReferralToken, ReferralConversion
from django.contrib.auth import get_user_model
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from .models import ReferralToken, ReferralConversion
from django.utils import timezone

from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone
from .models import ReferralToken, ReferralConversion


User = get_user_model()

SHARED_SECRET = getattr(settings, 'REFERRAL_SHARED_SECRET', None)
COOKIE_NAME = getattr(settings, 'REFERRAL_COOKIE_NAME', 'referral_token')




# @staff_member_required
# def referrals_dashboard_card(request):
#     active = ReferralToken.objects.filter(active=True, expires_at__gt=timezone.now()).count()
#     total_conv = ReferralConversion.objects.count()
#     conversion_rate = (total_conv/active) if active else 0
#     return render(request, 'referrals/dashboard_card.html', {
#         'active': active, 'total_conv': total_conv, 'conversion_rate': conversion_rate
#     })


def _check_shared_secret(request):
    """
    Very simple authentication for site-to-site API: a shared secret header or query param.
    """
    if not SHARED_SECRET:
        return False
    header = request.META.get('HTTP_X_REF_SHARED_SECRET') or request.GET.get('shared_secret')
    return header == SHARED_SECRET

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def api_record_conversion(request):
    """
    Endpoint to be called by a connected site when a purchase occurs.
    Accepts JSON body with:
      - token (optional): referral token code (cookie value)
      - referral_code (optional): referrer's referral_code (user.referral_code)
      - external_order_id (required)
      - amount (optional)
      - metadata (optional dict)

    Security: requests must include header X-REF-SHARED-SECRET matching settings.REFERRAL_SHARED_SECRET.

    Response:
      - 200 with conversion info on success
      - 403 if shared secret missing/invalid
      - 400 on bad request
    """
    # check shared secret
    if not _check_shared_secret(request):
        return HttpResponseForbidden("Invalid shared secret")

    try:
        body = request.data if hasattr(request, 'data') else json.loads(request.body.decode('utf-8') or '{}')
    except Exception:
        body = {}
    token_code = body.get('token') or request.POST.get('token') or request.GET.get('token')
    referral_code = body.get('referral_code') or request.POST.get('referral_code') or request.GET.get('referral_code')
    external_order_id = body.get('external_order_id') or request.POST.get('external_order_id') or request.GET.get('external_order_id')
    if not external_order_id:
        return JsonResponse({'error': 'external_order_id required'}, status=400)
    amount = body.get('amount')
    metadata = body.get('metadata') or {}

    referral_token = None
    referrer = None

    # prefer token (visitor cookie), then referral_code
    if token_code:
        try:
            referral_token = ReferralToken.objects.get(code=token_code, active=True)
            if referral_token.is_expired():
                referral_token.active = False
                referral_token.save()
                referral_token = None
            else:
                referrer = referral_token.referrer
        except ReferralToken.DoesNotExist:
            referral_token = None

    if not referrer and referral_code:
        try:
            referrer = User.objects.get(referral_code=referral_code)
        except User.DoesNotExist:
            referrer = None

    # create conversion record
    conv = ReferralConversion.objects.create(
        referral_token=referral_token,
        referrer=referrer,
        external_order_id=str(external_order_id),
        amount=(Decimal(str(amount)) if amount not in (None, '') else None),
        metadata=metadata or {}
    )

    return JsonResponse({
        'ok': True,
        'conversion_id': conv.id,
        'referrer_id': conv.referrer.id if conv.referrer else None,
        'referral_token': conv.referral_token.code if conv.referral_token else None,
        'external_order_id': conv.external_order_id
    }, status=200)


@api_view(['GET'])
def api_referral_metrics(request):
    """
    Simple dashboard JSON for active referrals and conversion rate.
    Returns:
      - active_referrals
      - total_conversions
      - conversions_last_30d
      - conversion_rate = total_conversions / active_referrals (or 0)
    """
    # allow staff users or valid shared secret for basic protection
    if not request.user.is_staff and not _check_shared_secret(request):
        return HttpResponseForbidden("Access denied")

    # make sure timezone is the module-level import (imported at top of file)
    active_referrals = ReferralToken.objects.filter(active=True, expires_at__gt=timezone.now()).count()
    total_conversions = ReferralConversion.objects.count()

    cutoff = timezone.now() - timezone.timedelta(days=30)
    conv_30 = ReferralConversion.objects.filter(created_at__gte=cutoff).count()

    conversion_rate = (total_conversions / active_referrals) if active_referrals else 0.0

    return JsonResponse({
        'active_referrals': active_referrals,
        'total_conversions': total_conversions,
        'conversions_last_30d': conv_30,
        'conversion_rate': float(conversion_rate),
    })


@staff_member_required
def referrals_dashboard_page(request):
    """
    Full dashboard page for referrals: KPI cards and a recent-conversions table.
    """
    now = timezone.now()
    active = ReferralToken.objects.filter(active=True, expires_at__gt=now).count()
    total_conv = ReferralConversion.objects.count()
    conv_30 = ReferralConversion.objects.filter(created_at__gte=(now - timezone.timedelta(days=30))).count()
    conversion_rate = (total_conv / active) if active else 0.0

    # recent conversions (paginated)
    recent_qs = ReferralConversion.objects.select_related('referrer', 'referral_token').order_by('-created_at')
    paginator = Paginator(recent_qs, 12)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    # data for mini chart: conversions per day for last 14 days
    days = []
    counts = []
    for i in range(13, -1, -1):
        day = (now - timezone.timedelta(days=i)).date()
        days.append(day.strftime('%b %d'))
        counts.append(ReferralConversion.objects.filter(created_at__date=day).count())

    return render(request, 'referrals/dashboard_page.html', {
        'active': active,
        'total_conv': total_conv,
        'conv_30': conv_30,
        'conversion_rate': conversion_rate,
        'chart_labels': days,
        'chart_data': counts,
        'page': page,
    })

# ---- Partner onboarding page (public or protected; currently staff-only) ----
# @staff_member_required
# def partner_onboarding(request):
#     """
#     Friendly partner integration instructions and code snippets.
#     Staff only by default; if you want public access remove decorator.
#     """
#     shared_secret = getattr(request._request, 'META', {}).get('HTTP_X_REF_SHARED_SECRET', None)
#     # We pass only static examples here; actual shared secret must be handled securely.
#     return render(request, 'referrals/partner_onboarding.html', {})


@staff_member_required
def partner_onboarding(request):
    """
    Friendly partner integration instructions and code snippets.

    This view is staff-only by default. It intentionally does NOT reveal the
    actual shared secret. If you want to display debugging info for staff,
    read it from settings (never expose it to public).
    """
    # Read headers / meta safely from the WSGIRequest
    incoming_secret = request.META.get('HTTP_X_REF_SHARED_SECRET')

    # Do NOT surface the real shared secret to templates. If you want to show
    # a placeholder or instructions, that's fine. For debug only you can read:
    configured_secret = getattr(settings, 'REFERRAL_SHARED_SECRET', None)

    context = {
        # provide request host/scheme for building examples in the template
        'host': request.get_host(),
        'scheme': request.scheme,
        # do NOT include the configured_secret in production templates;
        # I'm passing None so the template can show placeholders.
        'configured_secret_present': bool(configured_secret),
        'incoming_secret_present': bool(incoming_secret),
    }
    return render(request, 'referrals/partner_onboarding.html', context)


# ---- Simple partner dashboard: list conversions for a given referrer (by code) ----
@staff_member_required
def partner_dashboard(request):
    """
    Basic partner/merchant-facing page listing recent conversions and totals.
    Optionally supply ?referral_code=XYZ to filter by referrer.
    """
    referral_code = request.GET.get('referral_code')
    qs = ReferralConversion.objects.select_related('referrer', 'referral_token').all()
    if referral_code:
        qs = qs.filter(referrer__referral_code=referral_code)

    paginator = Paginator(qs.order_by('-created_at'), 20)
    page_number = request.GET.get('page', 1)
    page = paginator.get_page(page_number)

    return render(request, 'referrals/partner_dashboard.html', {
        'page': page, 'referral_code': referral_code
    })

