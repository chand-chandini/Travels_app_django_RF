import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from bookings.models import Bookings, Seat

# Initialize Razorpay INSIDE function to avoid import issues
# razorpay_client will be created inside each function

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    Create Razorpay order for payment
    """
    try:
        # Import razorpay INSIDE the function
        import razorpay
        
        # Initialize Razorpay client here
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        booking_id = request.data.get('booking_id')
        amount = request.data.get('amount')
        
        # Get booking and verify it belongs to user
        booking = Bookings.objects.get(id=booking_id, user=request.user)
        
        # Create Razorpay order
        order_data = {
            'amount': int(float(amount) * 100),  # Convert to paise
            'currency': 'INR',
            'receipt': f'booking_{booking_id}',
            'payment_capture': 1,
            'notes': {
                'booking_id': booking_id,
                'user_id': request.user.id,
                'user_email': request.user.email
            }
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        # Save payment record
        payment = Payment.objects.create(
            user=request.user,
            booking=booking,
            razorpay_order_id=order['id'],
            amount=amount,
            status='pending'
        )
        
        return Response({
            'success': True,
            'order_id': order['id'],
            'amount': int(float(amount) * 100),
            'key': settings.RAZORPAY_KEY_ID
        }, status=status.HTTP_200_OK)
        
    except Bookings.DoesNotExist:
        return Response({
            'error': 'Booking not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error creating order: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def payment_callback(request):
    """
    Verify payment after Razorpay callback
    """
    try:
        # Import razorpay INSIDE the function
        import razorpay
        
        # Initialize Razorpay client here
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        data = request.data
        
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': data.get('razorpay_order_id'),
            'razorpay_payment_id': data.get('razorpay_payment_id'),
            'razorpay_signature': data.get('razorpay_signature')
        }
        
        # Verify signature
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Get payment record
        payment = Payment.objects.get(razorpay_order_id=params_dict['razorpay_order_id'])
        
        # Update payment
        payment.razorpay_payment_id = params_dict['razorpay_payment_id']
        payment.razorpay_signature = params_dict['razorpay_signature']
        payment.status = 'success'
        payment.save()
        
        # Update booking
        booking = payment.booking
        booking.status = 'confirmed'
        booking.payment_id = params_dict['razorpay_payment_id']
        booking.save()
        
        # Mark seat as booked
        seat = booking.seat
        seat.is_booked = True
        seat.save()
        
        return Response({
            'status': 'success',
            'message': 'Payment verified successfully'
        }, status=status.HTTP_200_OK)
        
    except Payment.DoesNotExist:
        return Response({
            'status': 'failed',
            'error': 'Payment record not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Payment verification error: {str(e)}")
        return Response({
            'status': 'failed',
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)