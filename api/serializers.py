# api/serializers.py
from rest_framework import serializers

class SaleVerifySerializer(serializers.Serializer):
    external_order_id = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=10, required=False, default='USD')
    referral_token = serializers.CharField(max_length=64, required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)

class ReferralCheckSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=64)
