from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username','email','role','is_verified','is_approved')
    list_filter = ('role','is_verified','is_approved')
    actions = ['approve_users']

    def approve_users(self, request, queryset):
        count = queryset.update(is_approved=True)
        self.message_user(request, f"{count} users approved.")
