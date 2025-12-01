from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.conf import settings
from .models import ReferralToken
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()

DEFAULT_COOKIE_NAME = getattr(settings, 'REFERRAL_COOKIE_NAME', 'referral_token')
DEFAULT_COOKIE_AGE_DAYS = getattr(settings, 'REFERRAL_COOKIE_AGE_DAYS', 180)

class ReferralTrackingMiddleware:
    """
    Middleware to:
      - read ?ref=<referral_code> or ?referrer=<referral_code> on incoming requests
      - if present, resolve to a user and create or refresh a ReferralToken
      - set a cookie (REFERRAL_COOKIE_NAME) with the token.code valid for REFERRAL_COOKIE_AGE_DAYS
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _create_or_refresh_token(self, ref_code, request):
        # try to resolve referrer by referral_code on User
        try:
            ref_user = User.objects.get(referral_code=ref_code)
        except User.DoesNotExist:
            return None

        # prefer an existing active token for same referrer + same source_url if possible (to avoid many tokens)
        source = request.build_absolute_uri()[:2000] if hasattr(request, 'build_absolute_uri') else ''
        now = timezone.now()
        token = ReferralToken.objects.filter(referrer=ref_user, active=True, expires_at__gt=now).order_by('-created_at').first()
        if token:
            # refresh expiry
            token.expires_at = now + timedelta(days=DEFAULT_COOKIE_AGE_DAYS)
            token.source_url = source or token.source_url
            token.save()
            return token

        # create new token
        token = ReferralToken.objects.create(referrer=ref_user, source_url=source)
        return token

    def __call__(self, request):
        response = None
        # Look for ?ref= or ?referral= param (common patterns)
        ref_param = request.GET.get('ref') or request.GET.get('referral') or request.GET.get('referrer')
        cookie_name = getattr(settings, 'REFERRAL_COOKIE_NAME', DEFAULT_COOKIE_NAME)
        cookie_age_days = getattr(settings, 'REFERRAL_COOKIE_AGE_DAYS', DEFAULT_COOKIE_AGE_DAYS)

        token_code = request.COOKIES.get(cookie_name)
        token_obj = None

        # If a ref param is present, create/refresh token and set cookie
        if ref_param:
            token_obj = self._create_or_refresh_token(ref_param, request)
        elif token_code:
            # we already have cookie; try to fetch token and refresh expiry if needed
            try:
                token_obj = ReferralToken.objects.get(code=token_code)
                if token_obj.is_expired():
                    token_obj.active = False
                    token_obj.save()
                    token_obj = None
                else:
                    # extend expiry on activity
                    token_obj.expires_at = timezone.now() + timedelta(days=cookie_age_days)
                    token_obj.save()
            except ReferralToken.DoesNotExist:
                token_obj = None

        # Let the request process and then attach cookie to response
        response = self.get_response(request)

        if token_obj:
            # set cookie on response (HTTP only not necessary since JS may read? but for security set httponly=True)
            max_age = cookie_age_days * 24 * 60 * 60
            # secure flag only in production
            secure_flag = getattr(settings, 'REFERRAL_COOKIE_SECURE', False)
            response.set_cookie(cookie_name, token_obj.code, max_age=max_age, secure=secure_flag, httponly=True, samesite='Lax')
        return response
