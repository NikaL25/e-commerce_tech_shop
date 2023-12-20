from django.urls import path
from .import views

urlpatterns =[
    path('order_place/', views.order_place, name='order_place'),
    path('payments/', views.payments, name='payments'), 
    path('order_complete/', views.order_complete, name='order_complete'),

]