from django.urls import path
from .views import (HomeView, add_to_cart, CheckoutView,
                     ItemDetailView, remove_from_cart, OrderSummaryView, 
                     remove_single_item_from_cart, Home_plant_View, PaymentView, AddCouponView,RequestRefundView,
                     Home_plant_supply_View,Home_plant_decor_View,SearchView,user_order,
                     )


app_name = 'Order'
urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('home_plant/', Home_plant_View.as_view(), name='home_plant'),
    path('search/', SearchView.as_view(), name='search'),
    path('home_plant_supply/', Home_plant_supply_View.as_view(), name='home_plant_supply'),
    path('home_plant_decor/', Home_plant_decor_View.as_view(), name='home_plant_decor'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order_summary/', OrderSummaryView.as_view(), name='order_summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add_to_cart/<slug>/', add_to_cart, name='add_to_cart'),   
    path('user_order/', user_order, name='user_order'),
    path('add_coupont/', AddCouponView.as_view(), name='add_coupon'),   
    path('remove_from_cart/<slug>/', remove_from_cart, name='remove_from_cart'),
    path('remove_single_item_from_cart/<slug>/', remove_single_item_from_cart, name='remove_single_item_from_cart'),
    path('payment/<str:payment_option>/', PaymentView.as_view(), name='payment'),
    path('request_refund/', RequestRefundView.as_view(), name = 'request_refund')
]

