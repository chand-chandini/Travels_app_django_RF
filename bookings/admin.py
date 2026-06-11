from django.contrib import admin
from .models import Bus, Seat, Bookings, UserProfile, Review, Coupon

class BusAdmin(admin.ModelAdmin):
    list_display = ('bus_name', 'number', 'origin', 'destination', 'bus_type', 'price', 'rating')
    list_filter = ('bus_type', 'origin', 'destination')
    search_fields = ('bus_name', 'number', 'origin', 'destination')

class SeatAdmin(admin.ModelAdmin):
    list_display = ('seat_number', 'bus', 'is_booked', 'seat_type')
    list_filter = ('is_booked', 'seat_type', 'bus')
    search_fields = ('seat_number',)

class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'bus', 'seat', 'booking_time', 'status', 'total_amount')
    list_filter = ('status', 'booking_time')
    search_fields = ('user__username', 'bus__bus_name', 'seat__seat_number')

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'address')
    search_fields = ('user__username', 'phone')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('user', 'bus', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'bus__bus_name', 'comment')

class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_percent', 'valid_from', 'valid_to', 'is_active', 'used_count', 'max_uses')
    list_filter = ('is_active', 'valid_from', 'valid_to')
    search_fields = ('code',)
    readonly_fields = ('used_count',)
    
    fieldsets = (
        ('Coupon Information', {
            'fields': ('code', 'discount_percent', 'is_active')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_to')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'used_count')
        })
    )

    
admin.site.register(Bus, BusAdmin)
admin.site.register(Seat, SeatAdmin)
admin.site.register(Bookings, BookingAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Coupon, CouponAdmin)