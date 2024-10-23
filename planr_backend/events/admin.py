from django.contrib import admin
from .models import PrivateEvent, ProfessionalEvent, Service, EventRegistration, Wishlist

@admin.register(PrivateEvent)
class PrivateEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'date', 'time', 'max_participants')
    search_fields = ('title', 'location')
    list_filter = ('date', 'location')
    ordering = ('date', 'time')

@admin.register(ProfessionalEvent)
class ProfessionalEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'location', 'date', 'time', 'price', 'max_participants')
    search_fields = ('title', 'location', 'price')
    list_filter = ('date', 'location', 'price')
    ordering = ('date', 'time')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name',)
    ordering = ('name',)

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'registered_at', 'payment_status')
    search_fields = ('user__email', 'event__title')
    list_filter = ('payment_status', 'registered_at')
    ordering = ('-registered_at',)

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'event')
    search_fields = ('user__email', 'event__title')
    ordering = ('user',)

