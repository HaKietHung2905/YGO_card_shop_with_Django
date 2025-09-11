from django.urls import path
from . import admin_views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', admin_views.admin_dashboard, name='dashboard'),
    path('warehouse/', admin_views.admin_warehouse, name='warehouse'),
    path('posts/', admin_views.admin_posts, name='posts'),
    path('tournaments/', admin_views.admin_tournaments, name='tournaments'),
    path('orders/', admin_views.admin_orders, name='orders'),
    path('users/', admin_views.admin_users, name='users'),
    path('analytics/', admin_views.admin_analytics, name='analytics'),
    path('settings/', admin_views.admin_settings, name='settings'),
]