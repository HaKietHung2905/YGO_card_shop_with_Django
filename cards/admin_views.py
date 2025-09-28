from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Card, CardSet, CartItem, OtherProduct
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime
import json

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
def admin_card_sets(request):
    """Card Sets management page"""
    card_sets = CardSet.objects.all().order_by('-release_date')
    
    # Add statistics for each card set
    for card_set in card_sets:
        card_set.total_cards = Card.objects.filter(card_set=card_set).count()
        card_set.cards_in_stock = Card.objects.filter(card_set=card_set, stock_quantity__gt=0).count()
    
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        card_sets = card_sets.filter(
            Q(name__icontains=search_query) | 
            Q(code__icontains=search_query)
        )
    
    # Year filter
    year_filter = request.GET.get('year', '')
    if year_filter:
        card_sets = card_sets.filter(release_date__year=year_filter)
    
    # Pagination
    paginator = Paginator(card_sets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'card_sets': page_obj,
        'search_query': search_query,
        'year_filter': year_filter,
        'total_sets': CardSet.objects.count(),
        'sets_this_year': CardSet.objects.filter(release_date__year=datetime.now().year).count(),
        'upcoming_sets': CardSet.objects.filter(release_date__gt=datetime.now().date()).count(),
        'total_cards': Card.objects.count(),
        'today': datetime.now().date(),
    }
    return render(request, 'admin/warehouse/card_sets/index.html', context)

@staff_member_required
def admin_create_card_set(request):
    """Create a new card set"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip().upper()
            release_date = request.POST.get('release_date', '')
            description = request.POST.get('description', '').strip()
            
            # Validation
            if not name or not code or not release_date:
                return JsonResponse({
                    'success': False, 
                    'error': 'All required fields (name, code, release date) must be filled'
                })
            
            # Check if code already exists
            if CardSet.objects.filter(code=code).exists():
                return JsonResponse({
                    'success': False, 
                    'error': f'A card set with code "{code}" already exists'
                })
            
            # Validate date format
            try:
                release_date_obj = datetime.strptime(release_date, '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False, 
                    'error': 'Invalid date format'
                })
            
            # Create card set
            card_set = CardSet.objects.create(
                name=name,
                code=code,
                release_date=release_date_obj
            )
            
            messages.success(request, f'Card set "{card_set.name}" created successfully!')
            
            return JsonResponse({
                'success': True, 
                'message': f'Card set "{card_set.name}" created successfully!',
                'card_set_id': card_set.id,
                'redirect_url': f'/dashboard/warehouse/?set={card_set.id}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error creating card set: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def admin_edit_card_set(request, set_id):
    """Edit an existing card set"""
    card_set = get_object_or_404(CardSet, id=set_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip().upper()
            release_date = request.POST.get('release_date', '')
            
            # Validation
            if not name or not code or not release_date:
                return JsonResponse({
                    'success': False, 
                    'error': 'All required fields must be filled'
                })
            
            # Check if code already exists (excluding current set)
            if CardSet.objects.filter(code=code).exclude(id=set_id).exists():
                return JsonResponse({
                    'success': False, 
                    'error': f'A card set with code "{code}" already exists'
                })
            
            # Update card set
            card_set.name = name
            card_set.code = code
            card_set.release_date = datetime.strptime(release_date, '%Y-%m-%d').date()
            card_set.save()
            
            messages.success(request, f'Card set "{card_set.name}" updated successfully!')
            return JsonResponse({
                'success': True, 
                'message': f'Card set "{card_set.name}" updated successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error updating card set: {str(e)}'
            })
    
    # For GET requests, return card set data
    return JsonResponse({
        'success': True,
        'data': {
            'id': card_set.id,
            'name': card_set.name,
            'code': card_set.code,
            'release_date': card_set.release_date.isoformat(),
        }
    })

@staff_member_required
def admin_delete_card_set(request, set_id):
    """Delete a card set"""
    card_set = get_object_or_404(CardSet, id=set_id)
    
    if request.method == 'POST':
        try:
            # Check if there are cards in this set
            cards_count = Card.objects.filter(card_set=card_set).count()
            
            if cards_count > 0:
                return JsonResponse({
                    'success': False, 
                    'error': f'Cannot delete card set "{card_set.name}" because it contains {cards_count} cards. Please remove all cards first.'
                })
            
            card_set_name = card_set.name
            card_set.delete()
            
            messages.success(request, f'Card set "{card_set_name}" deleted successfully!')
            return JsonResponse({
                'success': True, 
                'message': f'Card set "{card_set_name}" deleted successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error deleting card set: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def admin_card_set_cards(request, set_id):
    """Get cards in a specific card set"""
    card_set = get_object_or_404(CardSet, id=set_id)
    cards = Card.objects.filter(card_set=card_set).order_by('name')
    
    # Convert to JSON-serializable format
    cards_data = []
    for card in cards:
        cards_data.append({
            'id': card.id,
            'name': card.name,
            'card_type': card.get_card_type_display(),
            'rarity': card.get_rarity_display(),
            'stock_quantity': card.stock_quantity,
            'price': str(card.price),
        })
    
    return JsonResponse({
        'success': True,
        'data': {
            'set_name': card_set.name,
            'set_code': card_set.code,
            'cards': cards_data,
        }
    })

@staff_member_required
def admin_card_sets_stats(request):
    """Get card sets statistics for dashboard"""
    total_sets = CardSet.objects.count()
    sets_this_year = CardSet.objects.filter(release_date__year=datetime.now().year).count()
    upcoming_sets = CardSet.objects.filter(release_date__gt=datetime.now().date()).count()
    total_cards = Card.objects.count()
    
    return JsonResponse({
        'success': True,
        'data': {
            'total_sets': total_sets,
            'sets_this_year': sets_this_year,
            'upcoming_sets': upcoming_sets,
            'total_cards': total_cards,
        }
    })

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
    
    # For GET requests, show confirmation page
    context = {
        'card': card,
    }
    return render(request, 'admin/warehouse/card_delete.html', context)


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
    return render(request, 'admin/posts/index.html', context)


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


@staff_member_required
def admin_other_products(request):
    """Other Products management page"""
    products = OtherProduct.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(sku__icontains=search_query) |
            Q(brand__icontains=search_query)
        )
    
    # Product type filter
    product_type_filter = request.GET.get('product_type', '')
    if product_type_filter:
        products = products.filter(product_type=product_type_filter)
    
    # Stock filter
    stock_filter = request.GET.get('stock', '')
    if stock_filter == 'low':
        products = products.filter(stock_quantity__lte=5)
    elif stock_filter == 'out':
        products = products.filter(stock_quantity=0)
    elif stock_filter == 'in':
        products = products.filter(stock_quantity__gt=0)
    
    # Ordering
    order_by = request.GET.get('order_by', 'name')
    if order_by in ['name', '-name', 'price', '-price', 'stock_quantity', '-stock_quantity', 'created_at', '-created_at']:
        products = products.order_by(order_by)
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'search_query': search_query,
        'product_type_filter': product_type_filter,
        'stock_filter': stock_filter,
        'order_by': order_by,
        'total_products': OtherProduct.objects.count(),
        'products_in_stock': OtherProduct.objects.filter(stock_quantity__gt=0).count(),
        'low_stock_products': OtherProduct.objects.filter(stock_quantity__lte=5, stock_quantity__gt=0).count(),
        'out_of_stock': OtherProduct.objects.filter(stock_quantity=0).count(),
        'product_type_choices': OtherProduct.PRODUCT_TYPE_CHOICES,
    }
    return render(request, 'admin/warehouse/other_products/index.html', context)

@staff_member_required
def admin_create_other_product(request):
    """Create a new other product"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            sku = request.POST.get('sku', '').strip().upper()
            product_type = request.POST.get('product_type', '')
            brand = request.POST.get('brand', '').strip()
            condition = request.POST.get('condition', 'new')
            price = request.POST.get('price', '')
            stock_quantity = request.POST.get('stock_quantity', '0')
            description = request.POST.get('description', '').strip()
            
            # Validation
            if not name or not sku or not product_type or not price:
                return JsonResponse({
                    'success': False, 
                    'error': 'Name, SKU, product type, and price are required'
                })
            
            # Check if SKU already exists
            if OtherProduct.objects.filter(sku=sku).exists():
                return JsonResponse({
                    'success': False, 
                    'error': f'A product with SKU "{sku}" already exists'
                })
            
            # Create product
            product = OtherProduct.objects.create(
                name=name,
                sku=sku,
                product_type=product_type,
                brand=brand,
                condition=condition,
                price=Decimal(price),
                stock_quantity=int(stock_quantity),
                description=description
            )
            
            # Handle image upload
            if 'image' in request.FILES:
                product.image = request.FILES['image']
                product.save()
            
            messages.success(request, f'Product "{product.name}" created successfully!')
            
            return JsonResponse({
                'success': True, 
                'message': f'Product "{product.name}" created successfully!',
                'product_id': product.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error creating product: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def admin_edit_other_product(request, product_id):
    """Edit an existing other product"""
    product = get_object_or_404(OtherProduct, id=product_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            sku = request.POST.get('sku', '').strip().upper()
            product_type = request.POST.get('product_type', '')
            brand = request.POST.get('brand', '').strip()
            condition = request.POST.get('condition', 'new')
            price = request.POST.get('price', '')
            stock_quantity = request.POST.get('stock_quantity', '0')
            description = request.POST.get('description', '').strip()
            
            # Validation
            if not name or not sku or not product_type or not price:
                return JsonResponse({
                    'success': False, 
                    'error': 'All required fields must be filled'
                })
            
            # Check if SKU already exists (excluding current product)
            if OtherProduct.objects.filter(sku=sku).exclude(id=product_id).exists():
                return JsonResponse({
                    'success': False, 
                    'error': f'A product with SKU "{sku}" already exists'
                })
            
            # Update product
            product.name = name
            product.sku = sku
            product.product_type = product_type
            product.brand = brand
            product.condition = condition
            product.price = Decimal(price)
            product.stock_quantity = int(stock_quantity)
            product.description = description
            
            # Handle image upload
            if 'image' in request.FILES:
                product.image = request.FILES['image']
                
            product.save()
            
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return JsonResponse({
                'success': True, 
                'message': f'Product "{product.name}" updated successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error updating product: {str(e)}'
            })
    
    # For GET requests, return product data
    return JsonResponse({
        'success': True,
        'data': {
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'product_type': product.product_type,
            'brand': product.brand,
            'condition': product.condition,
            'price': str(product.price),
            'stock_quantity': product.stock_quantity,
            'description': product.description,
        }
    })

@staff_member_required
def admin_delete_other_product(request, product_id):
    """Delete an other product"""
    product = get_object_or_404(OtherProduct, id=product_id)
    
    if request.method == 'POST':
        try:
            product_name = product.name
            product.delete()
            
            messages.success(request, f'Product "{product_name}" deleted successfully!')
            return JsonResponse({
                'success': True, 
                'message': f'Product "{product_name}" deleted successfully!'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': f'Error deleting product: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@staff_member_required
def admin_other_products_stats(request):
    """Get other products statistics"""
    total_products = OtherProduct.objects.count()
    products_in_stock = OtherProduct.objects.filter(stock_quantity__gt=0).count()
    low_stock_products = OtherProduct.objects.filter(stock_quantity__lte=5, stock_quantity__gt=0).count()
    out_of_stock = OtherProduct.objects.filter(stock_quantity=0).count()
    
    return JsonResponse({
        'success': True,
        'data': {
            'total_products': total_products,
            'products_in_stock': products_in_stock,
            'low_stock_products': low_stock_products,
            'out_of_stock': out_of_stock,
        }
    })

@staff_member_required
def admin_posts(request):
    """Enhanced Posts management"""
    # For now, create some dummy data since Post model might not exist yet
    context = {
        'posts': [],  # Empty list for now
        'total_posts': 0,
        'published_posts': 0,
        'draft_posts': 0,
        'total_views': 0,
        'search_query': '',
        'status_filter': '',
        'category_filter': '',
        'author_filter': '',
        'authors': [],
    }
    return render(request, 'admin/posts/index.html', context)

@staff_member_required
def admin_create_post(request):
    """Create a new post"""
    if request.method == 'POST':
        # For now, just redirect back with a message
        messages.success(request, 'Post creation functionality will be available once the Post model is created.')
        return redirect('admin_dashboard:posts')
    
    return redirect('admin_dashboard:posts')

@staff_member_required
def admin_edit_post(request, post_id):
    """Edit an existing post"""
    # For now, just redirect back with a message
    messages.info(request, f'Edit functionality for post {post_id} will be available once the Post model is created.')
    return redirect('admin_dashboard:posts')

@staff_member_required
def admin_delete_post(request, post_id):
    """Delete a post"""
    # For now, just redirect back with a message
    messages.info(request, f'Delete functionality for post {post_id} will be available once the Post model is created.')
    return redirect('admin_dashboard:posts')

@staff_member_required
def admin_bulk_post_action(request):
    """Handle bulk actions on posts"""
    if request.method == 'POST':
        action = request.POST.get('action')
        post_ids = request.POST.getlist('post_ids')
        
        # For now, just show what would happen
        messages.info(request, f'Bulk action "{action}" on {len(post_ids)} posts will be available once the Post model is created.')
    
    return redirect('admin_dashboard:posts')