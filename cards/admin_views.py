from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Card, CardSet, CartItem
from django.contrib.auth.models import User

@staff_member_required
def admin_dashboard(request):
    """Admin dashboard overview"""
    # Calculate real stats from your models
    total_cards = Card.objects.count()
    total_users = User.objects.count()
    recent_orders = CartItem.objects.select_related('user', 'card')[:5]
    
    context = {
        'total_revenue': 12847,  # You can calculate this from actual orders
        'orders_today': 147,
        'cards_in_stock': total_cards,
        'active_users': total_users,
        'recent_orders': recent_orders,
    }
    return render(request, 'admin/dashboard.html', context)

@staff_member_required
def admin_warehouse(request):
    """Warehouse management"""
    cards = Card.objects.select_related('card_set').all()[:20]
    card_sets = CardSet.objects.all()
    
    context = {
        'cards': cards,
        'card_sets': card_sets,
    }
    return render(request, 'admin/warehouse.html', context)

@staff_member_required
def admin_posts(request):
    """Posts management"""
    context = {}
    return render(request, 'admin/posts.html', context)

@staff_member_required
def admin_tournaments(request):
    """Tournament management"""
    context = {}
    return render(request, 'admin/tournaments.html', context)

@staff_member_required
def admin_orders(request):
    """Orders management"""
    orders = CartItem.objects.select_related('user', 'card').all()[:20]
    context = {
        'orders': orders,
    }
    return render(request, 'admin/orders.html', context)

@staff_member_required
def admin_users(request):
    """Users management"""
    users = User.objects.all()[:20]
    context = {
        'users': users,
    }
    return render(request, 'admin/users.html', context)

@staff_member_required
def admin_analytics(request):
    """Analytics and reports"""
    context = {}
    return render(request, 'admin/analytics.html', context)

@staff_member_required
def admin_settings(request):
    """Admin settings"""
    context = {}
    return render(request, 'admin/settings.html', context)