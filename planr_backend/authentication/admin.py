from django.contrib import admin
from .models import PasswordResetAttempt, Profile, Interest

@admin.register(PasswordResetAttempt)
class PasswordResetAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'requested_at', 'ip_address', 'user_agent')
    search_fields = ('user__email', 'user__phone_number', 'ip_address')
    list_filter = ('requested_at',)
    readonly_fields = ('requested_at', 'ip_address', 'user_agent')

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'birth_date', 'gender']
    search_fields = ['user__email', 'first_name']
