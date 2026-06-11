from rest_framework import serializers
from .models import Bus, Seat, Bookings, UserProfile, Review, Coupon
from django.contrib.auth.models import User

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user

class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ['id', 'seat_number', 'is_booked', 'seat_type']

class BusSerializer(serializers.ModelSerializer):
    seats = SeatSerializer(many=True, read_only=True)
    available_seats = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Bus
        fields = '__all__'
    
    def get_available_seats(self, obj):
        return obj.seats.filter(is_booked=False).count()
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(r.rating for r in reviews) / len(reviews)
        return 0

class BookingSerializer(serializers.ModelSerializer):
    bus = serializers.StringRelatedField()
    seat = SeatSerializer()
    user = serializers.StringRelatedField()
    bus_details = BusSerializer(source='bus', read_only=True)
    
    class Meta:
        model = Bookings
        fields = '__all__'
        read_only_fields = ['user', 'booking_time', 'bus', 'seat']

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'email', 'phone', 'address', 'date_of_birth']

class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'user_name', 'bus', 'rating', 'comment', 'created_at']
        read_only_fields = ['user', 'created_at']

class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ['code', 'discount_percent', 'valid_from', 'valid_to', 'is_active']