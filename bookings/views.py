
# Create your views here, logic of our application
# we do here authenticate,permissions,implenet generics,api_views,tokens,status,response

from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework import status,generics
from rest_framework.views import APIView
from .serializers import UserRegisterSerializer,BusSerializer,BookingSerializer
from rest_framework.response import Response
from .models import Bus,Seat,Bookings

class RegisterView(APIView): #creates get,put,delete,post method for us
    def post(self, request):
        serializer = UserRegisterSerializer(data= request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token':token.key}, status= status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    def post(self,request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username= username, password=password)

        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token':token.key,
                'user_id' : user.id
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error':'Invalid Credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        

class BusListCreateView(generics.ListCreateAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

class BusDetailview(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer

class BookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self,request):
        seat_id = request.data.get('seat')
        try:
            seat = Seat.objects.get(id = seat_id)
            if seat.is_booked:
                return Response({'error': 'Seat already booked'},status=status.HTTP_400_BAD_REQUEST)
            seat.is_booked = True
            seat.save()
            
            bookings = Bookings.objects.create(
                user = request.user,
                bus = seat.bus,
                seat= seat
            )
            serializer = BookingSerializer(bookings)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Seat.DoesNotExist:
            return Response({'error':'Seat not found'}, status=status.HTTP_404_NOT_FOUND)
        
class UserBookingView(APIView):
    permission_classes= [IsAuthenticated]

    def get(self, request, user_id):
        if request.user.id != user_id:
            return Response({'error': 'Unauthorized'},status=status.HTTP_401_UNAUTHORIZED)
        
        bookings = Bookings.objects.filter(user_id= user_id)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)


