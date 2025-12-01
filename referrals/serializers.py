from rest_framework import serializers
from .models import ReferralToken, ReferralConversion

class ReferralTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralToken
        fields = ['code', 'referrer', 'source_url', 'created_at', 'expires_at', 'active']

class ReferralConversionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralConversion
        fields = ['id', 'referral_token', 'referrer', 'external_order_id', 'amount', 'metadata', 'created_at']
