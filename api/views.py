# api/views.py

# from rest_framework.permissions import AllowAny
# DEFAULT_PERMISSION = AllowAny
# and use DEFAULT_PERMISSION or set permission_classes = [AllowAny] on the view


from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status



from decimal import Decimal
from django.db import transaction
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from referrals.models import ReferralToken, ReferralConversion
from referrals.auth import ApiKeyAuthentication

# NOTE about permissions:
# - For production, keep IsAuthenticated (JWT/Token).
# - For quick local tests you can switch to AllowAny or implement shared-secret auth.
DEFAULT_PERMISSION = IsAuthenticated


class ReferralCheckView(APIView):
    """
    GET /api/referral/check/?token=...
    POST /api/referral/check/   { "token": "..." }

    Returns basic info about a referral token. Accepts both GET and POST to
    be tolerant of different clients/tests.
    """
    permission_classes = [IsAuthenticated]

    def _lookup_token(self, token_code):
        if not token_code:
            return None
        try:
            token = ReferralToken.objects.get(code=token_code)
            return token
        except ReferralToken.DoesNotExist:
            return None

    def get(self, request, *args, **kwargs):
        token_code = request.query_params.get('token') or request.query_params.get('referral_token')
        token = self._lookup_token(token_code)
        if not token:
            return Response({'valid': False}, status=status.HTTP_200_OK)

        data = {
            'valid': token.active and not token.is_expired(),
            'referrer_username': getattr(token.referrer, 'username', None),
            'referrer_id': getattr(token.referrer, 'pk', None),
            'expires_at': token.expires_at.isoformat() if token.expires_at else None,
            'source_url': token.source_url,
            'code': token.code,
        }
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        # Accept token from JSON body for clients that POST
        token_code = request.data.get('token') or request.data.get('referral_token')
        token = self._lookup_token(token_code)
        if not token:
            return Response({'valid': False}, status=status.HTTP_200_OK)

        data = {
            'valid': token.active and not token.is_expired(),
            'referrer_username': getattr(token.referrer, 'username', None),
            'referrer_id': getattr(token.referrer, 'pk', None),
            'expires_at': token.expires_at.isoformat() if token.expires_at else None,
            'source_url': token.source_url,
            'code': token.code,
        }
        return Response(data, status=status.HTTP_200_OK)


class SaleVerifyView(APIView):
    """
    POST /api/sale/verify/
    Body (JSON):
      {
        "order_id": "ABC123",
        "amount": 99.99,
        "currency": "USD",
        "referral_token": "token-code-here",
        "metadata": {"product": "T-shirt"}
      }
    This view:
     - resolves referral token -> referrer
     - normalizes amount -> Decimal
     - puts unknown fields (currency, product details) into metadata
     - creates ReferralConversion
    """
    permission_classes = [DEFAULT_PERMISSION]

    def post(self, request, *args, **kwargs):
        data = request.data or {}

        # Resolve token and referrer
        token_code = data.get('referral_token') or data.get('token') or data.get('referral_code')
        token = None
        referrer = None
        if token_code:
            try:
                token = ReferralToken.objects.get(code=token_code, active=True)
                if token.is_expired():
                    token = None
                else:
                    referrer = token.referrer
            except ReferralToken.DoesNotExist:
                token = None

        # Map fields
        external_order_id = data.get('external_order_id') or data.get('order_id') or None

        amount = None
        if 'amount' in data and data.get('amount') is not None:
            try:
                amount = Decimal(str(data.get('amount')))
            except Exception:
                return Response({'detail': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

        # prepare metadata
        metadata = {}
        if isinstance(data.get('metadata'), dict):
            metadata.update(data.get('metadata'))

        # move currency into metadata rather than passing it as a model kwarg
        if 'currency' in data:
            metadata['currency'] = data.get('currency')

        # add any extra non-model items you want to keep
        if 'customer_email' in data:
            metadata['customer_email'] = data.get('customer_email')

        conv_kwargs = {
            'referral_token': token,
            'referrer': referrer,
            'external_order_id': external_order_id,
            'amount': amount,
            'metadata': metadata,
        }

        with transaction.atomic():
            conv = ReferralConversion.objects.create(**conv_kwargs)

        return Response({
            'status': 'ok',
            'conversion_id': conv.pk,
        }, status=status.HTTP_201_CREATED)
