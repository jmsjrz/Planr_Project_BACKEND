from django.contrib import admin
from .models import PrivateEvent, EventRegistration, Wishlist


@admin.register(PrivateEvent)
class PrivateEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'date', 'time', 'max_participants')
    search_fields = ('title', 'location')
    list_filter = ('date', 'location')
    ordering = ('date', 'time')


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registered_at')
    search_fields = ('user__email', 'event__title')
    list_filter = ('registered_at',)
    ordering = ('registered_at',)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'event')
    search_fields = ('user__email', 'event__title')
    ordering = ('user',)

