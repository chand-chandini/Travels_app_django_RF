from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Bus(models.Model):
    bus_name = models.CharField(max_length=100)
    number = models.CharField(max_length=20, unique=True)
    origin = models.CharField(max_length=50)
    destination = models.CharField(max_length=50)
    features = models.TextField()
    start_time = models.TimeField()
    reach_Time = models.TimeField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    no_of_seats = models.PositiveBigIntegerField()

    def __str__(self):
        return f"{self.bus_name} {self.number} {self.origin} {self.destination}" #these will display there in backend when we create a bus object

class Seat(models.Model):
    bus = models.ForeignKey('Bus', on_delete=models.CASCADE, related_name='seats') #using foreign key to link seat to bus
    seat_number = models.CharField(max_length=10)
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.bus} {self.seat_number}"
    

class Bookings(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE)
    seat = models.ForeignKey(Seat,on_delete=models.CASCADE)
    booking_time = models.DateTimeField(auto_now_add=True)

    def __str__(self): #this will display the user, bus and seat information when we create a booking object in the backend
        return f"{self.user.username}-{self.bus.bus_name}-{self.bus.start_time}-{self.bus.reach_Time}-{self.seat.seat_number}"

