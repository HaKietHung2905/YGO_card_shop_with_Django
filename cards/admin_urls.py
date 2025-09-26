# In cards/admin_urls.py
from django.urls import path
from . import admin_views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', admin_views.admin_dashboard, name='dashboard'),  # This now shows warehouse data
    path('warehouse/', admin_views.admin_warehouse, name='warehouse'),  # Keep this for legacy or redirect to dashboard
    path('warehouse/card/edit/<int:card_id>/', admin_views.admin_edit_card, name='edit_card'),
    path('warehouse/card/delete/<int:card_id>/', admin_views.admin_delete_card, name='delete_card'),
    path('warehouse/update-stock/', admin_views.admin_update_stock, name='update_stock'),
    
    path('posts/', admin_views.admin_posts, name='posts'),
    path('tournaments/', admin_views.admin_tournaments, name='tournaments'),
    path('orders/', admin_views.admin_orders, name='orders'),
    path('users/', admin_views.admin_users, name='users'),
    path('analytics/', admin_views.admin_analytics, name='analytics'),
    path('settings/', admin_views.admin_settings, name='settings'),
]