from django.contrib import admin
from .models import Commission, Wallet, WalletTransaction
from django.utils import timezone
from django.contrib import messages

@admin.action(description="Approve selected commissions and credit wallets")
def approve_commissions(modeladmin, request, queryset):
    count = 0
    for comm in queryset:
        if comm.status == Commission.STATUS_PENDING:
            try:
                comm.approve(approver=request.user)
                count += 1
            except Exception as e:
                modeladmin.message_user(request, f"Failed to approve commission {comm.id}: {e}", level=messages.ERROR)
    modeladmin.message_user(request, f"{count} commissions approved and wallets credited", level=messages.SUCCESS)

@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
    list_display = ('id', 'telemarketer', 'amount', 'source', 'status', 'sale_reference', 'created_at', 'approved_at')
    list_filter = ('status', 'source', 'created_at')
    search_fields = ('telemarketer__username', 'sale_reference')
    actions = [approve_commissions]

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username',)

@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'tx_type', 'amount', 'note', 'created_at')
    list_filter = ('tx_type', 'created_at')
    search_fields = ('wallet__user__username', 'note')
