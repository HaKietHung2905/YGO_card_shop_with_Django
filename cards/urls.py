from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# Import the signup view
try:
    from .auth_views import signup_view
except ImportError:
    # Fallback if auth_views.py doesn't exist yet
    def signup_view(request):
        from django.http import HttpResponse
        return HttpResponse("Signup view not implemented yet")

urlpatterns = [
    # Main pages
    path('', views.home, name='home'),
    path('cards/', views.card_list, name='card_list'),
    path('card-detail/<int:pk>/', views.card_detail, name='card_detail'),  # Updated URL pattern
    
    # Cart functionality
    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:pk>/', views.update_cart_quantity, name='update_cart_quantity'),  # ← ADD THIS LINE
    
    # Order URLs
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/process/', views.process_checkout, name='process_checkout'),
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),


    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', signup_view, name='signup'),
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]