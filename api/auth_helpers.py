from django.conf import settings
from referrals.models import ApiServiceKey  # your model that stores keys
from rest_framework.exceptions import AuthenticationFailed

def get_request_service_key(request):
    # prefer header X-API-KEY
    key = request.headers.get('X-API-KEY') or request.headers.get('X-Api-Key') \
          or request.META.get('HTTP_X_API_KEY')

    if key:
        try:
            return ApiServiceKey.objects.get(key=key, active=True)
        except ApiServiceKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key")
    # fallback: old shared-secret header (optional)
    shared = request.headers.get('X-REF-SHARED-SECRET') or request.META.get('HTTP_X_REF_SHARED_SECRET')
    if shared:
        if shared == getattr(settings, 'REFERRAL_SHARED_SECRET', None):
            return 'internal-shared'
        raise AuthenticationFailed("Invalid shared secret")
    raise AuthenticationFailed("No service credentials provided")