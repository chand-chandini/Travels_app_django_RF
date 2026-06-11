from django.urls import path
from . import views

urlpatterns = [
    path('create-order/', views.create_order, name='create_order'),
    path('callback/', views.payment_callback, name='payment_callback'),
]