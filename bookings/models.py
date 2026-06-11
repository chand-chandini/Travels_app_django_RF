from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

# Define choices at the top of the file
BUS_TYPES = [
    ('ac', 'AC'),
    ('non-ac', 'Non-AC'),
    ('sleeper', 'Sleeper'),
    ('seater', 'Seater'),
]

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
]

REFUND_STATUS_CHOICES = [
    ('not_applied', 'Not Applied'),
    ('processing', 'Processing'),
    ('completed', 'Completed'),
    ('failed', 'Failed'),
]

# Create your models here.

class Bus(models.Model):
    bus_name = models.CharField(max_length=100)
    number = models.CharField(max_length=20, unique=True)
    origin = models.CharField(max_length=50)
    destination = models.CharField(max_length=50)
    features = models.TextField(blank=True)
    start_time = models.TimeField()
    reach_time = models.TimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    no_of_seats = models.PositiveBigIntegerField()
    bus_type = models.CharField(max_length=20, choices=BUS_TYPES, default='seater')
    amenities = models.JSONField(default=list, blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.bus_name} {self.number} ({self.origin} to {self.destination})"

class Seat(models.Model):
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)
    is_booked = models.BooleanField(default=False)
    seat_type = models.CharField(max_length=20, default='regular')

    def __str__(self):
        return f"{self.bus.bus_name} - Seat {self.seat_number}"

class Bookings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    booking_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    passenger_name = models.CharField(max_length=100, blank=True, default='')
    passenger_phone = models.CharField(max_length=15, blank=True, default='')
    
    # Refund fields
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    refund_status = models.CharField(max_length=20, choices=REFUND_STATUS_CHOICES, default='not_applied')
    refund_date = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.user.username} - {self.bus.bus_name} - Seat {self.seat.seat_number}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return self.user.username

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'bus']
    
    def __str__(self):
        return f"{self.user.username} - {self.bus.bus_name} - {self.rating} stars"

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_uses = models.IntegerField(default=100)
    used_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.code