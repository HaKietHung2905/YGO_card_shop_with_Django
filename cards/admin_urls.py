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
    
    # Order Management URLs - NEW
    path('orders/', admin_views.admin_orders, name='orders'),
    path('orders/<int:order_id>/', admin_views.admin_order_detail, name='order_detail'),
    path('orders/<int:order_id>/update-status/', admin_views.admin_update_order_status, name='update_order_status'),
    path('orders/<int:order_id>/update-payment/', admin_views.admin_update_payment_status, name='update_payment_status'),
    path('orders/statistics/', admin_views.admin_order_statistics, name='order_statistics'),
 
    # Other Products Management URLs
    path('warehouse/other-products/', admin_views.admin_other_products, name='other_products'),
    path('warehouse/other-products/create/', admin_views.admin_create_other_product, name='create_other_product'),
    path('warehouse/other-products/edit/<int:product_id>/', admin_views.admin_edit_other_product, name='edit_other_product'),
    path('warehouse/other-products/delete/<int:product_id>/', admin_views.admin_delete_other_product, name='delete_other_product'),
    path('warehouse/other-products/stats/', admin_views.admin_other_products_stats, name='other_products_stats'),

    path('tournaments/', admin_views.admin_tournaments, name='tournaments'),
    path('orders/', admin_views.admin_orders, name='orders'),
    path('users/', admin_views.admin_users, name='users'),
    path('analytics/', admin_views.admin_analytics, name='analytics'),
    path('settings/', admin_views.admin_settings, name='settings'),

    # Posts Management URLs
    path('posts/', admin_views.admin_posts, name='posts'),
    path('posts/create/', admin_views.admin_create_post, name='create_post'),
    path('posts/edit/<int:post_id>/', admin_views.admin_edit_post, name='edit_post'),
    path('posts/delete/<int:post_id>/', admin_views.admin_delete_post, name='delete_post'),
    path('posts/bulk-action/', admin_views.admin_bulk_post_action, name='bulk_post_action'),

    # User Management URLs
    path('users/', admin_views.admin_users, name='users'),
    path('users/create/', admin_views.create_user, name='user_create'),
    path('users/<int:user_id>/', admin_views.admin_user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', admin_views.admin_edit_user, name='edit_user'),
    path('users/<int:user_id>/toggle-status/', admin_views.admin_toggle_user_status, name='toggle_user_status'),
   
    # Tournament URLs
    path('tournaments/', admin_views.admin_tournaments, name='tournaments'),
    path('tournaments/create/', admin_views.create_tournament, name='create_tournament'),
    path('tournaments/<int:tournament_id>/', admin_views.tournament_detail, name='tournament_detail'),
    path('tournaments/<int:tournament_id>/edit/', admin_views.edit_tournament, name='edit_tournament'),
    path('tournaments/<int:tournament_id>/delete/', admin_views.delete_tournament, name='delete_tournament'),
    
    # Settings URLs
    path('settings/', admin_views.admin_settings, name='settings'),
    path('settings/update/', admin_views.update_settings, name='update_settings'),
    path('settings/clear-cache/', admin_views.clear_cache, name='clear_cache'),
    path('settings/shipping/', admin_views.admin_shipping_settings, name='shipping_settings'),
]