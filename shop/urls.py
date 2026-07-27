from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'), # মেইন হোমপেজ
    path('product/<int:product_id>/', views.product_detail, name='product_detail'), # প্রোডাক্ট ডিটেইলস পেজ
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart_view, name='cart_view'),
    path('checkout/', views.checkout_view, name='checkout_view'),
    
    path('seller/dashboard/', views.seller_dashboard, name='seller_dashboard'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('delete-cart-item/<int:product_id>/', views.delete_cart_item, name='delete_cart_item'),
    path('order/update/<int:order_id>/<str:status>/', views.update_order_status, name='update_order_status'),
    path('gallery/', views.gallery_view, name='gallery'), # গ্যালারি পেজ লিংক
    path('about/', views.about_view, name='about'), # অ্যাবাউট আস পেজ লিংক
    path('contact/', views.contact_view, name='contact'),
]