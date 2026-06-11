from django.urls import path
from .views import (
    RegisterView, LoginView, BusListCreateView, BookingView, 
    BusDetailview, UserBookingView, UserProfileView, ReviewCreateView,
    BusReviewsView, CancelBookingView, ValidateCouponView, MyBookingsView
)

urlpatterns = [
    path('buses/', BusListCreateView.as_view(), name='buslist'),
    path('buses/<int:pk>/', BusDetailview.as_view(), name='bus-detail'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('user/<int:user_id>/bookings/', UserBookingView.as_view(), name='user-bookings'),
    path('booking/', BookingView.as_view(), name='booking'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('reviews/', ReviewCreateView.as_view(), name='create-review'),
    path('buses/<int:bus_id>/reviews/', BusReviewsView.as_view(), name='bus-reviews'),
    path('bookings/<int:booking_id>/cancel/', CancelBookingView.as_view(), name='cancel-booking'),  # Add this
    path('validate-coupon/', ValidateCouponView.as_view(), name='validate-coupon'),
    path('my-bookings/', MyBookingsView.as_view(), name='my-bookings'),
    path('validate-coupon/', ValidateCouponView.as_view(), name='validate-coupon'),
]