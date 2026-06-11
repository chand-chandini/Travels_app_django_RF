from django.contrib.auth import authenticate
from django.db.models import Q
from datetime import datetime, timedelta
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserRegisterSerializer, BusSerializer, BookingSerializer, UserProfileSerializer, ReviewSerializer, CouponSerializer
from .models import Bus, Seat, Bookings, UserProfile, Review, Coupon
from decimal import Decimal
from django.utils import timezone
from django.conf import settings
from rest_framework import status
import razorpay
from payments.models import Payment


razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.id
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class BusListCreateView(generics.ListCreateAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
    
    def get_queryset(self):
        queryset = Bus.objects.all()
        
        origin = self.request.query_params.get('origin')
        if origin:
            queryset = queryset.filter(origin__icontains=origin)
        
        destination = self.request.query_params.get('destination')
        if destination:
            queryset = queryset.filter(destination__icontains=destination)
        
        bus_type = self.request.query_params.get('bus_type')
        if bus_type and bus_type != 'all':
            queryset = queryset.filter(bus_type=bus_type)
        
        min_price = self.request.query_params.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        max_price = self.request.query_params.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(bus_name__icontains=search) |
                Q(origin__icontains=search) |
                Q(destination__icontains=search)
            )
        
        return queryset

class BusDetailview(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

class BookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        seat_id = request.data.get('seat')
        passenger_name = request.data.get('passenger_name', '')
        passenger_phone = request.data.get('passenger_phone', '')
        total_amount = request.data.get('total_amount')
        coupon_code = request.data.get('coupon_code', None)
        
        try:
            seat = Seat.objects.get(id=seat_id)
            if seat.is_booked:
                return Response({'error': 'Seat already booked'}, status=status.HTTP_400_BAD_REQUEST)
            
            original_amount = total_amount or float(seat.bus.price)
            discount_amount = 0
            discount_percent = 0
            
            # Apply coupon if provided
            if coupon_code:
                from django.utils import timezone
                try:
                    coupon = Coupon.objects.get(
                        code=coupon_code,
                        is_active=True,
                        valid_from__lte=timezone.now(),
                        valid_to__gte=timezone.now()
                    )
                    
                    if coupon.used_count < coupon.max_uses:
                        discount_percent = coupon.discount_percent
                        discount_amount = (original_amount * discount_percent) / 100
                        coupon.used_count += 1
                        coupon.save()
                    else:
                        return Response({'error': 'Coupon usage limit exceeded'}, status=400)
                        
                except Coupon.DoesNotExist:
                    return Response({'error': 'Invalid coupon code'}, status=400)
            
            final_amount = original_amount - discount_amount
            
            # Create booking
            booking = Bookings.objects.create(
                user=request.user,
                bus=seat.bus,
                seat=seat,
                passenger_name=passenger_name,
                passenger_phone=passenger_phone,
                total_amount=final_amount,
                status='pending'
            )
            
            serializer = BookingSerializer(booking)
            return Response({
                'booking': serializer.data,
                'discount': {
                    'applied': discount_percent > 0,
                    'percent': discount_percent,
                    'amount': discount_amount,
                    'original_amount': original_amount,
                    'final_amount': final_amount
                }
            }, status=status.HTTP_201_CREATED)
            
        except Seat.DoesNotExist:
            return Response({'error': 'Seat not found'}, status=status.HTTP_404_NOT_FOUND)

class UserBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        if request.user.id != user_id:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        bookings = Bookings.objects.filter(user_id=user_id).order_by('-booking_time')
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)
    
    def put(self, request):
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ReviewSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            bus = Bus.objects.get(id=request.data['bus'])
            reviews = Review.objects.filter(bus=bus)
            avg_rating = sum(r.rating for r in reviews) / len(reviews)
            bus.rating = avg_rating
            bus.total_reviews = len(reviews)
            bus.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

class BusReviewsView(APIView):
    def get(self, request, bus_id):
        reviews = Review.objects.filter(bus_id=bus_id).order_by('-created_at')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

class CancelBookingView(APIView):
    permission_classes = [IsAuthenticated]
    
    def calculate_refund_amount(self, booking):
        """Calculate refund based on cancellation time"""
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        now = timezone.now()
        
        # Get bus start time
        departure_time = booking.bus.start_time
        
        # Create departure datetime for today
        departure_datetime = datetime.combine(now.date(), departure_time)
        
        # Make it timezone aware
        departure_datetime = timezone.make_aware(departure_datetime)
        
        # If departure passed today, use tomorrow
        if departure_datetime < now:
            departure_datetime = departure_datetime + timedelta(days=1)
        
        # Calculate hours before departure
        hours_before = (departure_datetime - now).total_seconds() / 3600
        
        total_amount = float(booking.total_amount) if booking.total_amount else 0
        
        if hours_before >= 48:
            return total_amount, 100
        elif hours_before >= 24:
            return total_amount * 0.75, 75
        elif hours_before >= 12:
            return total_amount * 0.50, 50
        elif hours_before >= 2:
            return total_amount * 0.25, 25
        else:
            return 0, 0
    
    def post(self, request, booking_id):
        try:
            from django.utils import timezone
            
            booking = Bookings.objects.get(id=booking_id, user=request.user)
            
            if booking.status == 'cancelled':
                return Response({'error': 'Booking already cancelled'}, status=400)
            
            cancellation_reason = request.data.get('reason', 'Cancelled by user')
            refund_amount, refund_percent = self.calculate_refund_amount(booking)
            
            # Update booking
            booking.status = 'cancelled'
            booking.cancellation_reason = cancellation_reason
            booking.refund_amount = refund_amount
            booking.refund_status = 'completed' if refund_amount > 0 else 'not_applied'
            booking.refund_date = timezone.now()
            booking.save()
            
            # Free up the seat
            booking.seat.is_booked = False
            booking.seat.save()
            
            return Response({
                'message': 'Booking cancelled successfully',
                'refund': {
                    'amount': refund_amount,
                    'percentage': refund_percent,
                    'status': f'Refund of ₹{refund_amount} processed' if refund_amount > 0 else 'No refund applicable'
                }
            }, status=200)
            
        except Bookings.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=404)
        except Exception as e:
            print(f"ERROR: {str(e)}")
            return Response({'error': str(e)}, status=500)

class ValidateCouponView(APIView):
    def post(self, request):
        code = request.data.get('code')
        amount = request.data.get('amount', 0)
        
        try:
            from django.utils import timezone
            
            coupon = Coupon.objects.get(
                code=code,
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_to__gte=timezone.now()
            )
            
            if coupon.used_count >= coupon.max_uses:
                return Response({
                    'valid': False,
                    'error': 'Coupon usage limit exceeded'
                }, status=400)
            
            # Calculate discounted amount
            discount_amount = (amount * coupon.discount_percent) / 100
            final_amount = amount - discount_amount
            
            return Response({
                'valid': True,
                'discount_percent': coupon.discount_percent,
                'code': coupon.code,
                'discount_amount': discount_amount,
                'final_amount': final_amount
            })
            
        except Coupon.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Invalid or expired coupon'
            }, status=400)

class MyBookingsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        bookings = Bookings.objects.filter(user=request.user).order_by('-booking_time')
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)