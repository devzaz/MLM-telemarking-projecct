# referrals/admin.py
from django.contrib import admin
from .models import ReferralToken, ReferralConversion, ApiServiceKey

# Admin for ApiServiceKey
@admin.register(ApiServiceKey)
class ApiServiceKeyAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_active", "created_at")
    readonly_fields = ("key", "created_at")
    search_fields = ("name", "user__username")
    list_filter = ("is_active",)

# Admin for ReferralToken
@admin.register(ReferralToken)
class ReferralTokenAdmin(admin.ModelAdmin):
    list_display = ("short_code", "referrer", "source_url", "active", "created_at", "expires_at")
    search_fields = ("code", "referrer__username")
    list_filter = ("active", "created_at")

    # helpful computed column to show short code in list_display
    def short_code(self, obj):
        return obj.code[:8]
    short_code.short_description = "Code"

# Admin for ReferralConversion
@admin.register(ReferralConversion)
class ReferralConversionAdmin(admin.ModelAdmin):
    list_display = ("external_order_id", "referrer", "amount", "created_at", "referral_token_display")
    search_fields = ("external_order_id", "referrer__username")
    list_filter = ("created_at",)

    def referral_token_display(self, obj):
        return obj.referral_token.code[:8] if obj.referral_token else "—"
    referral_token_display.short_description = "Token"
