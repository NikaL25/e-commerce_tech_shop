from django.urls import path
from .import views


urlpatterns =[
    path('', views.store, name='store'),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>', views.product_detail, name='product_detail'),
    path('search/',views.search, name='search'),
    path('products/', views.product_list, name='product_list'),
    path('filter_by_price/', views.filter_by_price, name='filter_by_price'),


   

]