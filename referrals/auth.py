# referrals/auth.py
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .models import ApiServiceKey

class ApiKeyAuthentication(BaseAuthentication):
    """
    Accepts header:
      Authorization: Token <key>
    Checks ApiServiceKey.key and is_active.
    """

    keyword = 'Token'

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header:
            return None  # allow other authenticators (SessionAuth, JWT, etc.) to try

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            return None

        key = parts[1].strip()
        try:
            api_key = ApiServiceKey.objects.get(key=key, is_active=True)
        except ApiServiceKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')

        # optionally link to a User for permissions; if there is no User:
        user = api_key.user
        # If user is None, return an AnonymousUser-like principal or create a pseudo-user.
        # For simplicity if no user set, we return None user but still consider authenticated via key.
        # DRF expects (user, auth) tuple; user must be a User instance or an object with is_authenticated True.
        if user is None:
            # create a lightweight object with is_authenticated True and username = api key name
            class _ServiceUser:
                is_authenticated = True
                def __init__(self, name):
                    self.username = name
            user = _ServiceUser(api_key.name)

        return (user, api_key)
