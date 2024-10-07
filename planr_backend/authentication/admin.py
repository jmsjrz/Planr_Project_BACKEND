from django.contrib import admin
from .models import PasswordResetAttempt

@admin.register(PasswordResetAttempt)
class PasswordResetAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'requested_at', 'ip_address', 'user_agent')
    search_fields = ('user__email', 'user__phone_number', 'ip_address')
    list_filter = ('requested_at',)
    readonly_fields = ('requested_at', 'ip_address', 'user_agent')
