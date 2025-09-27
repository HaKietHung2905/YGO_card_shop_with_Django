# In cards/admin_urls.py
from django.urls import path
from . import admin_views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', admin_views.admin_dashboard, name='dashboard'),  # This now shows warehouse data
    # Warehouse Management
    path('warehouse/', admin_views.admin_warehouse, name='warehouse'),
    path('warehouse/card/edit/<int:card_id>/', admin_views.admin_edit_card, name='edit_card'),
    path('warehouse/card/delete/<int:card_id>/', admin_views.admin_delete_card, name='delete_card'),
    path('warehouse/update-stock/', admin_views.admin_update_stock, name='update_stock'),
    
    # Card Sets (under warehouse)
    path('warehouse/card-sets/', admin_views.admin_card_sets, name='card_sets'),
    path('warehouse/card-sets/create/', admin_views.admin_create_card_set, name='create_card_set'),
    path('warehouse/card-sets/edit/<int:set_id>/', admin_views.admin_edit_card_set, name='edit_card_set'),
    path('warehouse/card-sets/delete/<int:set_id>/', admin_views.admin_delete_card_set, name='delete_card_set'),
    path('warehouse/card-sets/<int:set_id>/cards/', admin_views.admin_card_set_cards, name='card_set_cards'),
    path('warehouse/card-sets/stats/', admin_views.admin_card_sets_stats, name='card_sets_stats'),
    
    
    path('posts/', admin_views.admin_posts, name='posts'),
    path('tournaments/', admin_views.admin_tournaments, name='tournaments'),
    path('orders/', admin_views.admin_orders, name='orders'),
    path('users/', admin_views.admin_users, name='users'),
    path('analytics/', admin_views.admin_analytics, name='analytics'),
    path('settings/', admin_views.admin_settings, name='settings'),
]