from django.contrib import admin
from .models import Profile, Interest

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'account_type')
    search_fields = ('first_name', 'last_name', 'user__email')

@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
