from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Card, CardSet, CartItem
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime


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
    """Warehouse management with manual card creation"""
    
    # Initialize forms
    form = None
    card_set_form = None
    bulk_form = None 

    # Handle form submissions
    if request.method == 'POST':
        print("=== DEBUG: POST request received ===")
        print(f"POST data: {dict(request.POST)}")
        print(f"FILES data: {dict(request.FILES)}")
        
        if 'create_card' in request.POST:
            print("=== DEBUG: create_card detected ===")
            try:
                # Get form data
                name = request.POST.get('name', '').strip()
                print(f"Card name: '{name}'")
                description = request.POST.get('description', '').strip()
                card_type = request.POST.get('card_type', '')
                rarity = request.POST.get('rarity', '')
                card_set_id = request.POST.get('card_set', '')
                condition = request.POST.get('condition', '')
                price = request.POST.get('price', '')
                stock_quantity = request.POST.get('stock_quantity', '')
                image = request.FILES.get('image')
                
                # Monster stats (optional)
                attack = request.POST.get('attack', '') or None
                defense = request.POST.get('defense', '') or None
                level = request.POST.get('level', '') or None
                
                # Validation
                errors = []
                
                if not name:
                    errors.append("Card name is required")
                if not card_type:
                    errors.append("Card type is required")
                if not rarity:
                    errors.append("Rarity is required")
                if not card_set_id:
                    errors.append("Card set is required")
                if not condition:
                    errors.append("Condition is required")
                if not price:
                    errors.append("Price is required")
                if not stock_quantity:
                    errors.append("Stock quantity is required")
                
                # Validate card_type
                valid_card_types = [choice[0] for choice in Card.CARD_TYPE_CHOICES]
                if card_type not in valid_card_types:
                    errors.append("Invalid card type")
                
                # Validate rarity
                valid_rarities = [choice[0] for choice in Card.RARITY_CHOICES]
                if rarity not in valid_rarities:
                    errors.append("Invalid rarity")
                
                # Validate condition
                valid_conditions = [choice[0] for choice in Card.CONDITION_CHOICES]
                if condition not in valid_conditions:
                    errors.append("Invalid condition")
                
                # Validate card set exists
                try:
                    card_set = CardSet.objects.get(id=card_set_id)
                except CardSet.DoesNotExist:
                    errors.append("Invalid card set")
                
                # Validate numeric fields
                try:
                    price = Decimal(price)
                    if price < 0:
                        errors.append("Price cannot be negative")
                except (ValueError, TypeError):
                    errors.append("Invalid price format")
                
                try:
                    stock_quantity = int(stock_quantity)
                    if stock_quantity < 0:
                        errors.append("Stock quantity cannot be negative")
                except (ValueError, TypeError):
                    errors.append("Invalid stock quantity format")
                
                # Validate monster stats if monster card
                if card_type == 'monster':
                    if attack is not None:
                        try:
                            attack = int(attack)
                            if attack < 0:
                                errors.append("Attack cannot be negative")
                        except (ValueError, TypeError):
                            errors.append("Invalid attack value")
                    
                    if defense is not None:
                        try:
                            defense = int(defense)
                            if defense < 0:
                                errors.append("Defense cannot be negative")
                        except (ValueError, TypeError):
                            errors.append("Invalid defense value")
                    
                    if level is not None:
                        try:
                            level = int(level)
                            if level < 1 or level > 12:
                                errors.append("Level must be between 1 and 12")
                        except (ValueError, TypeError):
                            errors.append("Invalid level value")
                
                # If no errors, create the card
                if not errors:
                    try:
                        card = Card.objects.create(
                            name=name,
                            description=description,
                            card_type=card_type,
                            rarity=rarity,
                            card_set=card_set,
                            condition=condition,
                            price=price,
                            stock_quantity=stock_quantity,
                            image=image,
                            attack=attack,
                            defense=defense,
                            level=level
                        )
                        
                        messages.success(request, f'Card "{card.name}" created successfully!')
                        return redirect('admin_dashboard:warehouse')
                        
                    except Exception as e:
                        messages.error(request, f'Error creating card: {str(e)}')
                else:
                    for error in errors:
                        messages.error(request, error)
                        
            except Exception as e:
                messages.error(request, f'Unexpected error: {str(e)}')
        
        elif 'create_card_set' in request.POST:
            try:
                # Get card set data
                name = request.POST.get('name', '').strip()
                code = request.POST.get('code', '').strip().upper()
                release_date = request.POST.get('release_date', '')
                
                # Validation
                errors = []
                
                if not name:
                    errors.append("Set name is required")
                if not code:
                    errors.append("Set code is required")
                if not release_date:
                    errors.append("Release date is required")
                
                # Check if code already exists
                if code and CardSet.objects.filter(code=code).exists():
                    errors.append("A card set with this code already exists")
                
                # Validate date format
                try:
                    release_date = datetime.strptime(release_date, '%Y-%m-%d').date()
                except ValueError:
                    errors.append("Invalid date format")
                
                # If no errors, create the card set
                if not errors:
                    try:
                        card_set = CardSet.objects.create(
                            name=name,
                            code=code,
                            release_date=release_date
                        )
                        
                        messages.success(request, f'Card set "{card_set.name}" created successfully!')
                        return redirect('admin_dashboard:warehouse')
                        
                    except Exception as e:
                        messages.error(request, f'Error creating card set: {str(e)}')
                else:
                    for error in errors:
                        messages.error(request, error)
                        
            except Exception as e:
                messages.error(request, f'Unexpected error: {str(e)}')
    else:
        # Initialize empty forms for GET requests
        from .forms import CardForm, CardSetForm, BulkCardUploadForm
        form = CardForm()
        card_set_form = CardSetForm()
        bulk_form = BulkCardUploadForm()

    # Handle search and filtering for GET requests
    cards = Card.objects.select_related('card_set').all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        cards = cards.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(card_set__name__icontains=search_query)
        )
    
    # Filter by card type
    card_type_filter = request.GET.get('card_type', '')
    if card_type_filter:
        cards = cards.filter(card_type=card_type_filter)
    
    # Filter by rarity
    rarity_filter = request.GET.get('rarity', '')
    if rarity_filter:
        cards = cards.filter(rarity=rarity_filter)
    
    # Filter by card set
    card_set_filter = request.GET.get('card_set', '')
    if card_set_filter:
        cards = cards.filter(card_set_id=card_set_filter)
    
    # Filter by stock status
    stock_filter = request.GET.get('stock', '')
    if stock_filter == 'low':
        cards = cards.filter(stock_quantity__lte=5)
    elif stock_filter == 'out':
        cards = cards.filter(stock_quantity=0)
    elif stock_filter == 'in':
        cards = cards.filter(stock_quantity__gt=0)

    # Ordering
    order_by = request.GET.get('order_by', 'name')
    if order_by in ['name', '-name', 'price', '-price', 'stock_quantity', '-stock_quantity', 'created_at', '-created_at']:
        cards = cards.order_by(order_by)
    else:
        cards = cards.order_by('name')

    # Pagination
    paginator = Paginator(cards, 20)  # 20 cards per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all card sets for filters and dropdowns
    card_sets = CardSet.objects.all().order_by('name')
    
    context = {
        'cards': page_obj,
        'card_sets': card_sets, 
        'form': form,
        'card_set_form': card_set_form,
        'bulk_form': bulk_form,
        'search_query': search_query,
        'card_type_filter': card_type_filter,
        'rarity_filter': rarity_filter,
        'card_set_filter': card_set_filter,
        'stock_filter': stock_filter,
        'order_by': order_by,
        'card_type_choices': Card.CARD_TYPE_CHOICES,
        'rarity_choices': Card.RARITY_CHOICES,
    }
    return render(request, 'admin/warehouse/index.html', context)

@staff_member_required
def admin_edit_card(request, card_id):
    """Edit an existing card"""
    card = get_object_or_404(Card, id=card_id)
    
    if request.method == 'POST':
        try:
            # Get form data (similar to create_card logic)
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            card_type = request.POST.get('card_type', '')
            rarity = request.POST.get('rarity', '')
            card_set_id = request.POST.get('card_set', '')
            condition = request.POST.get('condition', '')
            price = request.POST.get('price', '')
            stock_quantity = request.POST.get('stock_quantity', '')
            image = request.FILES.get('image')
            
            # Monster stats (optional)
            attack = request.POST.get('attack', '') or None
            defense = request.POST.get('defense', '') or None
            level = request.POST.get('level', '') or None
            
            # Update card fields
            card.name = name
            card.description = description
            card.card_type = card_type
            card.rarity = rarity
            card.card_set = CardSet.objects.get(id=card_set_id)
            card.condition = condition
            card.price = Decimal(price)
            card.stock_quantity = int(stock_quantity)
            
            if image:
                card.image = image
            
            if card_type == 'monster':
                card.attack = int(attack) if attack else None
                card.defense = int(defense) if defense else None
                card.level = int(level) if level else None
            else:
                card.attack = None
                card.defense = None
                card.level = None
            
            card.save()
            
            messages.success(request, f'Card "{card.name}" updated successfully!')
            return redirect('admin_dashboard:warehouse')
            
        except Exception as e:
            messages.error(request, f'Error updating card: {str(e)}')
    
    card_sets = CardSet.objects.all().order_by('name')
    
    context = {
        'card': card,
        'card_sets': card_sets,
        'is_edit': True,
    }
    return render(request, 'admin/warehouse/edit_card.html', context)


@staff_member_required
def admin_delete_card(request, card_id):
    """Delete a card"""
    card = get_object_or_404(Card, id=card_id)
    
    if request.method == 'POST':
        card_name = card.name
        card.delete()
        messages.success(request, f'Card "{card_name}" deleted successfully!')
        return redirect('admin_dashboard:warehouse')
    
    context = {
        'card': card,
    }
    return render(request, 'admin/delete_card.html', context)


@staff_member_required
def admin_update_stock(request):
    """AJAX endpoint to update card stock"""
    if request.method == 'POST':
        try:
            card_id = request.POST.get('card_id')
            new_stock = int(request.POST.get('stock_quantity', 0))
            
            card = get_object_or_404(Card, id=card_id)
            card.stock_quantity = new_stock
            card.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Stock updated for {card.name}',
                'new_stock': new_stock
            })
        except (ValueError, TypeError):
            return JsonResponse({
                'success': False,
                'message': 'Invalid stock quantity'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


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