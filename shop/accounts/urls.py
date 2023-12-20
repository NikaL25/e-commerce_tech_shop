from django.urls import path
from .import views


urlpatterns = [

    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/',views.dashboard, name='dashboard'),
    path('',views.dashboard, name='dashboard'),

    path('activate/<uidb64>[0-9A-Za-z_\-]/?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/' , views.activate, name='activate'),
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('resetpassword_validate/<uidb64>/<token>/' , views.resetpassword_validate, name='resetpassword_validate'),
    path('resetPassword/', views.resetPassword, name='resetPassword'),

    path('my_orders/', views.my_orders, name='my_orders'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('order_detail/<int:order_id>/', views.order_detail, name='order_detail'),
    path('dashboard/edit-order/<int:orders_number>/', views.edit_order, name='edit_order'),
    path('dashboard/delete-order/<str:orders_number>/', views.delete_order, name='delete_order'),

    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete_product/<int:product_id>/', views.delete_product, name='delete_product'),

    path('change_password/', views.change_password, name='change_password'),


]