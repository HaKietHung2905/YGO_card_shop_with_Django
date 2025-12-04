from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import Card, CardSet, CartItem, OtherProduct, Tournament
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from decimal import Decimal
from datetime import datetime
import json
from .models import Order, SiteSettings
from django.db.models import Sum, Count
from django import forms
from django.template.exceptions import TemplateDoesNotExist

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
            image = request.FILES.get('image')
            
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
                release_date=release_date_obj,
                image=image
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
            image = request.FILES.get('image')
            
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
            
            if image:
                card_set.image = image
                
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
            'image_url': card_set.image.url if card_set.image else None,
            'description': getattr(card_set, 'description', '') # Assuming description might be added later or handled elsewhere
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
    return render(request, 'admin/warehouse/cards/index.html', context)

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
    return render(request, 'admin/warehouse/cards/card_edit.html', context)


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
    return render(request, 'admin/warehouse/cards/card_delete.html', context)


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
    return render(request, 'admin/tournaments/index.html', context)


@staff_member_required
def admin_analytics(request):
    """Analytics and reports"""
    context = {}
    return render(request, 'admin/analytics.html', context)


@staff_member_required
def admin_settings(request):
    """Admin settings"""
    context = {}
    return render(request, 'admin/settings/index.html', context)


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
            # Update product fields
            product.name = request.POST.get('name', '').strip()
            product.product_type = request.POST.get('product_type', '')
            product.brand = request.POST.get('brand', '').strip()
            product.sku = request.POST.get('sku', '').strip().upper()
            product.price = Decimal(request.POST.get('price', '0'))
            product.stock_quantity = int(request.POST.get('stock_quantity', '0'))
            product.condition = request.POST.get('condition', 'new')
            product.description = request.POST.get('description', '').strip()
            
            # Handle image upload
            if 'image' in request.FILES:
                product.image = request.FILES['image']
            
            product.save()
            
            messages.success(request, f'Sản phẩm "{product.name}" đã được cập nhật thành công!')
            return redirect('admin_dashboard:other_products')
            
        except Exception as e:
            messages.error(request, f'Lỗi khi cập nhật sản phẩm: {str(e)}')
    
    # For GET requests, render the edit page
    context = {
        'product': product,
        'product_type_choices': OtherProduct.PRODUCT_TYPE_CHOICES,
    }
    return render(request, 'admin/warehouse/other_products/edit.html', context)

@staff_member_required
def admin_delete_other_product(request, product_id):
    """Delete an other product"""
    product = get_object_or_404(OtherProduct, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Sản phẩm "{product_name}" đã được xóa thành công!')
        return redirect('admin_dashboard:other_products')
    
    # For GET requests, show confirmation page
    context = {
        'product': product,
    }
    return render(request, 'admin/warehouse/other_products/delete.html', context)

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
@staff_member_required
def admin_orders(request):
    """Enhanced orders management with filtering and search"""
    orders = Order.objects.select_related('user').prefetch_related('items').all()
    
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(shipping_full_name__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Filter by payment status
    payment_filter = request.GET.get('payment', '')
    if payment_filter:
        orders = orders.filter(payment_status=payment_filter)
    
    # Date range filter
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    if date_from:
        orders = orders.filter(created_at__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__lte=date_to)
    
    # Ordering - IMPORTANT: Order BEFORE pagination
    order_by = request.GET.get('order_by', '-created_at')
    orders = orders.order_by(order_by)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # DEBUG: Check what's in the page
    print(f"DEBUG: Page has {len(page_obj)} orders")
    for order in page_obj:
        print(f"DEBUG: Order ID={order.id}, PK={order.pk}, Number={order.order_number}")
    
    # Statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    processing_orders = Order.objects.filter(status='processing').count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    context = {
        'orders': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'date_from': date_from,
        'date_to': date_to,
        'order_by': order_by,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'total_revenue': total_revenue,
        'status_choices': Order.STATUS_CHOICES,
    }
    return render(request, 'admin/orders/index.html', context)
    
@staff_member_required
def admin_order_detail(request, order_id):
    """View detailed information about a specific order"""
    order = get_object_or_404(Order, id=order_id)
    order_items = order.items.select_related('card', 'other_product').all()
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'admin/orders/order_detail.html', context)


@staff_member_required
def admin_update_order_status(request, order_id):
    """Update order status"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes', '')
        
        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            
            # Add admin notes if provided
            if admin_notes:
                if order.admin_notes:
                    order.admin_notes += f"\n\n{admin_notes}"
                else:
                    order.admin_notes = admin_notes
            
            order.save()
            messages.success(request, f'Order status updated from {old_status} to {new_status}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('admin_dashboard:order_detail', order_id=order_id)


@staff_member_required
def admin_update_payment_status(request, order_id):
    """Update payment status"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        payment_status = request.POST.get('payment_status')
        
        if payment_status in ['paid', 'unpaid', 'refunded']:
            order.payment_status = payment_status
            order.save()
            messages.success(request, f'Payment status updated to {payment_status}')
        else:
            messages.error(request, 'Invalid payment status')
    
    return redirect('admin_dashboard:order_detail', order_id=order_id)


@staff_member_required
def admin_order_statistics(request):
    """Display order statistics and analytics"""
    from django.db.models.functions import TruncDate
    from datetime import datetime, timedelta
    
    # Date range for statistics (last 30 days by default)
    days = int(request.GET.get('days', 30))
    start_date = datetime.now() - timedelta(days=days)
    
    # Orders by status
    orders_by_status = Order.objects.values('status').annotate(count=Count('id')).order_by('status')
    
    # Orders by date (for chart)
    orders_by_date = Order.objects.filter(created_at__gte=start_date).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('date')
    
    # Revenue statistics
    total_revenue = Order.objects.filter(payment_status='paid').aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    revenue_this_month = Order.objects.filter(
        payment_status='paid',
        created_at__month=datetime.now().month,
        created_at__year=datetime.now().year
    ).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Top customers
    top_customers = Order.objects.values('user__username', 'user__email').annotate(
        total_orders=Count('id'),
        total_spent=Sum('total_amount')
    ).order_by('-total_spent')[:10]
    
    context = {
        'days': days,
        'orders_by_status': orders_by_status,
        'orders_by_date': orders_by_date,
        'total_revenue': total_revenue,
        'revenue_this_month': revenue_this_month,
        'top_customers': top_customers,
    }
    return render(request, 'admin/order_statistics.html', context)

# Add this function to your cards/admin_views.py file

@staff_member_required
def admin_users(request):
    """User management dashboard"""
    from datetime import datetime, timedelta
    
    # Get all users with related data
    users = User.objects.all().order_by('-date_joined')
    
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Role filter
    role_filter = request.GET.get('role', '')
    if role_filter == 'staff':
        users = users.filter(is_staff=True)
    elif role_filter == 'regular':
        users = users.filter(is_staff=False, is_superuser=False)
    elif role_filter == 'superuser':
        users = users.filter(is_superuser=True)
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    
    # Calculate statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_count = User.objects.filter(is_staff=True).count()
    
    # New users this month
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_month = User.objects.filter(date_joined__gte=current_month_start).count()
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'total_users': total_users,
        'active_users': active_users,
        'staff_count': staff_count,
        'new_users_month': new_users_month,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'admin/users/index.html', context)


@staff_member_required
def admin_user_detail(request, user_id):
    """View user details"""
    user = get_object_or_404(User, id=user_id)
    
    # Get user's orders
    user_orders = Order.objects.filter(user=user).order_by('-created_at')[:10]
    
    # Get user's cart items
    cart_items = CartItem.objects.filter(user=user)
    
    # Calculate statistics
    total_orders = Order.objects.filter(user=user).count()
    total_spent = Order.objects.filter(
        user=user, 
        payment_status='paid'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'user_detail': user,
        'user_orders': user_orders,
        'cart_items': cart_items,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }
    
    return render(request, 'admin/users/user_detail.html', context)


@staff_member_required
def admin_edit_user(request, user_id):
    """Edit user details"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Update user information
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.is_active = request.POST.get('is_active') == 'on'
        user.is_staff = request.POST.get('is_staff') == 'on'
        
        try:
            user.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('admin_dashboard:user_detail', user_id=user.id)
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    context = {
        'user_to_edit': user,
    }
    
    return render(request, 'admin/users/user_edit.html', context)


@staff_member_required
def admin_toggle_user_status(request, user_id):
    """Toggle user active status"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        
        # Don't allow deactivating superusers
        if user.is_superuser:
            messages.error(request, 'Cannot deactivate superuser accounts')
            return redirect('admin_dashboard:users')
        
        user.is_active = not user.is_active
        user.save()
        
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.username} has been {status}')
    
    return redirect('admin_dashboard:users')


class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user

@staff_member_required
def create_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} has been created successfully!')
            return redirect('admin_dashboard:users')
    else:
        form = CustomUserCreationForm()
    
    context = {
        'form': form,
        'page_title': 'Create User'
    }
    return render(request, 'admin/users/user_create.html', context)

@staff_member_required
def admin_tournaments(request):
    # Get all tournaments
    tournaments = Tournament.objects.all().annotate(
        participants_count=Count('participants')
    ).order_by('-date', '-start_time')
    
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        tournaments = tournaments.filter(
            Q(name__icontains=search_query) |
            Q(format__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        tournaments = tournaments.filter(status=status_filter)
    
    # Date filter
    date_from = request.GET.get('date_from', '')
    if date_from:
        tournaments = tournaments.filter(date__gte=date_from)
    
    # Calculate statistics
    total_tournaments = Tournament.objects.count()
    upcoming_count = Tournament.objects.filter(status='upcoming').count()
    ongoing_count = Tournament.objects.filter(status='ongoing').count()
    total_participants = Tournament.objects.aggregate(
        total=Count('participants')
    )['total'] or 0
    
    # Pagination
    paginator = Paginator(tournaments, 10)
    page_number = request.GET.get('page')
    tournaments_page = paginator.get_page(page_number)
    
    context = {
        'tournaments': tournaments_page,
        'search_query': search_query,
        'status_filter': status_filter,
        'date_from': date_from,
        'total_tournaments': total_tournaments,
        'upcoming_count': upcoming_count,
        'ongoing_count': ongoing_count,
        'total_participants': total_participants,
    }
    
    return render(request, 'admin/tournaments/index.html', context)


@staff_member_required
def create_tournament(request):
    if request.method == 'POST':
        try:
            tournament = Tournament.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                date=request.POST.get('date'),
                start_time=request.POST.get('start_time'),
                location=request.POST.get('location', ''),
                format=request.POST.get('format', 'standard'),
                max_participants=request.POST.get('max_participants') or None,
                entry_fee=request.POST.get('entry_fee', 0),
                prize_pool=request.POST.get('prize_pool') or None,
                organizer=request.user
            )
            messages.success(request, f'Tournament "{tournament.name}" created successfully!')
            return redirect('admin_dashboard:tournaments')
        except Exception as e:
            messages.error(request, f'Error creating tournament: {str(e)}')
    
    context = {
        'formats': Tournament.FORMAT_CHOICES,
        'statuses': Tournament.STATUS_CHOICES,
    }
    return render(request, 'admin/create_tournament.html', context)

# Tournament Detail View
@staff_member_required
def tournament_detail(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    participants = tournament.participants.all()
    
    context = {
        'tournament': tournament,
        'participants': participants,
    }
    return render(request, 'admin/tournament_detail.html', context)

# Edit Tournament View
@staff_member_required
def edit_tournament(request, tournament_id):
    tournament = get_object_or_404(Tournament, id=tournament_id)
    
    if request.method == 'POST':
        try:
            tournament.name = request.POST.get('name')
            tournament.description = request.POST.get('description', '')
            tournament.date = request.POST.get('date')
            tournament.start_time = request.POST.get('start_time')
            tournament.location = request.POST.get('location', '')
            tournament.format = request.POST.get('format', 'standard')
            tournament.max_participants = request.POST.get('max_participants') or None
            tournament.entry_fee = request.POST.get('entry_fee', 0)
            tournament.prize_pool = request.POST.get('prize_pool') or None
            tournament.status = request.POST.get('status', 'upcoming')
            tournament.save()
            
            messages.success(request, f'Tournament "{tournament.name}" updated successfully!')
            return redirect('admin_dashboard:tournaments')
        except Exception as e:
            messages.error(request, f'Error updating tournament: {str(e)}')
    
    context = {
        'tournament': tournament,
        'formats': Tournament.FORMAT_CHOICES,
        'statuses': Tournament.STATUS_CHOICES,
    }
    return render(request, 'admin/edit_tournament.html', context)

# Delete Tournament View
@staff_member_required
@require_POST
def delete_tournament(request, tournament_id):
    try:
        tournament = get_object_or_404(Tournament, id=tournament_id)
        tournament_name = tournament.name
        tournament.delete()
        return JsonResponse({
            'success': True,
            'message': f'Tournament "{tournament_name}" deleted successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
    
@staff_member_required
def create_tournament(request):
    if request.method == 'POST':
        try:
            tournament = Tournament.objects.create(
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                date=request.POST.get('date'),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time') or None,
                location=request.POST.get('location', ''),
                format=request.POST.get('format', 'standard'),
                max_participants=request.POST.get('max_participants') or None,
                entry_fee=request.POST.get('entry_fee', 0),
                prize_pool=request.POST.get('prize_pool') or None,
                rules=request.POST.get('rules', ''),
                prize_structure=request.POST.get('prize_structure', ''),
                organizer=request.user
            )
            messages.success(request, f'Tournament "{tournament.name}" created successfully!')
            return redirect('admin_dashboard:tournaments')
        except Exception as e:
            messages.error(request, f'Error creating tournament: {str(e)}')
    
    from datetime import date
    context = {
        'formats': Tournament.FORMAT_CHOICES,
        'statuses': Tournament.STATUS_CHOICES,
        'today': date.today(),
    }
    return render(request, 'admin/tournaments/tournament_create.html', context)

@staff_member_required
def admin_settings(request):
    """Display admin settings page"""
    # Get settings from database or use defaults
    # You can create a Settings model or use django-constance for this
    
    context = {
        # General settings
        'site_name': 'Yu-Gi-Oh Card Shop',
        'maintenance_mode': False,
        'allow_registration': True,
        'email_notifications': True,
        
        # Shop settings
        'currency': 'USD',
        'tax_rate': 0,
        'min_order_amount': 0,
        'low_stock_threshold': 5,
        
        # Tournament settings
        'auto_approve_registrations': True,
        'default_max_participants': 32,
        'registration_deadline_hours': 24,
        
        # System stats
        'db_size': '245 MB',
        'cache_size': '12 MB',
        'uptime': '15 days',
        'version': '1.0.0',
    }
    
    return render(request, 'admin/settings/index.html', context)

@staff_member_required
@require_POST
def update_settings(request):
    """Update settings based on form submission"""
    section = request.POST.get('section')
    
    try:
        if section == 'general':
            # Update general settings
            # site_name = request.POST.get('site_name')
            # maintenance_mode = request.POST.get('maintenance_mode') == 'on'
            # Save to database or config
            messages.success(request, 'General settings updated successfully!')
            
        elif section == 'shop':
            # Update shop settings
            messages.success(request, 'Shop settings updated successfully!')
            
        elif section == 'tournament':
            # Update tournament settings
            messages.success(request, 'Tournament settings updated successfully!')
            
    except Exception as e:
        messages.error(request, f'Error updating settings: {str(e)}')
    
    return redirect('admin_dashboard:settings')

@staff_member_required
@require_POST
def clear_cache(request):
    """Clear application cache"""
    try:
        from django.core.cache import cache
        cache.clear()
        return JsonResponse({'success': True, 'message': 'Cache cleared successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


@staff_member_required
def admin_settings(request):
    """Display admin settings page"""
    settings = SiteSettings.get_settings()
    
    context = {
        # General settings
        'site_name': settings.site_name,
        'maintenance_mode': settings.maintenance_mode,
        'allow_registration': settings.allow_registration,
        'email_notifications': settings.email_notifications,
        'theme_mode': settings.theme_mode,
        
        # Shop settings
        'currency': settings.currency,
        'tax_rate': settings.tax_rate,
        'min_order_amount': settings.min_order_amount,
        'low_stock_threshold': settings.low_stock_threshold,
        
        # Tournament settings
        'auto_approve_registrations': settings.auto_approve_registrations,
        'default_max_participants': settings.default_max_participants,
        'registration_deadline_hours': settings.registration_deadline_hours,
        
        # System stats
        'db_size': '245 MB',
        'cache_size': '12 MB',
        'uptime': '15 days',
        'version': '1.0.0',
    }
    
    return render(request, 'admin/settings/index.html', context)

@staff_member_required
@require_POST
def update_settings(request):
    """Update settings based on form submission"""
    section = request.POST.get('section')
    settings = SiteSettings.get_settings()
    
    try:
        if section == 'general':
            settings.site_name = request.POST.get('site_name', settings.site_name)
            settings.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
            settings.allow_registration = request.POST.get('allow_registration') == 'on'
            settings.email_notifications = request.POST.get('email_notifications') == 'on'
            settings.theme_mode = request.POST.get('theme_mode', 'light')
            settings.save()
            messages.success(request, 'General settings updated successfully!')
            
        elif section == 'shop':
            settings.currency = request.POST.get('currency', 'VND')
            settings.tax_rate = request.POST.get('tax_rate', 0)
            settings.min_order_amount = request.POST.get('min_order_amount', 0)
            settings.low_stock_threshold = request.POST.get('low_stock_threshold', 5)
            settings.save()
            messages.success(request, 'Shop settings updated successfully!')
            
        elif section == 'tournament':
            settings.auto_approve_registrations = request.POST.get('auto_approve_registrations') == 'on'
            settings.default_max_participants = request.POST.get('default_max_participants', 32)
            settings.registration_deadline_hours = request.POST.get('registration_deadline_hours', 24)
            settings.save()
            messages.success(request, 'Tournament settings updated successfully!')
            
    except Exception as e:
        messages.error(request, f'Error updating settings: {str(e)}')
    
    return redirect('admin_dashboard:settings')
# In cards/admin_views.py

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_create_other_product(request):
    # Create the form class inline if not defined elsewhere
    from django import forms
    from .models import OtherProduct
    
    class OtherProductForm(forms.ModelForm):
        class Meta:
            model = OtherProduct
            fields = ['name', 'description', 'product_type', 'brand', 'sku', 'price', 'stock_quantity', 'image']
            widgets = {
                'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tên sản phẩm'}),
                'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
                'product_type': forms.Select(attrs={'class': 'form-select'}),
                'brand': forms.TextInput(attrs={'class': 'form-control'}),
                'sku': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Để trống để tự động tạo'}),
                'price': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
                'stock_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'value': '0'}),
                'image': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['brand'].required = False
            self.fields['sku'].required = False
            self.fields['description'].required = False
            self.fields['image'].required = False

    if request.method == 'POST':
        form = OtherProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            
            # Auto-generate SKU if not provided
            if not product.sku:
                product.save()  # Save first to get ID
                sku_prefix = product.get_product_type_display()[:3].upper()
                product.sku = f"{sku_prefix}-{product.pk:05d}"
                product.save()
            else:
                product.save()
            
            messages.success(request, f'Sản phẩm "{product.name}" đã được tạo thành công!')
            return redirect('admin_dashboard:other_products')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin.')
    else:
        # Handle GET request - display empty form
        form = OtherProductForm()
    
    context = {
        'form': form,
        'title': 'Thêm Sản Phẩm Mới',
        'action': 'create',
    }
    
    # Try to render the template
    try:
        return render(request, 'admin/warehouse/other_products/form.html', context)
    except TemplateDoesNotExist:
        # If template doesn't exist, create a basic form
        return render(request, 'admin/warehouse/other_products/index.html', context)  # Fallback to a template you know exists

@staff_member_required
def admin_shipping_settings(request):
    """Manage shipping settings"""
    from .models import ShippingSettings
    from .forms import ShippingSettingsForm
    
    settings = ShippingSettings.get_settings()
    
    if request.method == 'POST':
        form = ShippingSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Đã cập nhật cài đặt vận chuyển thành công!')
            return redirect('admin_dashboard:shipping_settings')
        else:
            messages.error(request, 'Vui lòng kiểm tra lại thông tin.')
    else:
        form = ShippingSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
        'page_title': 'Cài Đặt Vận Chuyển',
    }
    return render(request, 'admin/settings/shipping_settings.html', context)

@staff_member_required
def update_order_status(request, order_id):
    """Update order status"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        note = request.POST.get('note', '')
        
        if new_status in dict(Order.STATUS_CHOICES):
            old_status = order.get_status_display()
            order.status = new_status
            order.save()
            
            # Log the status change (optional)
            log_message = f"Cập nhật trạng thái từ '{old_status}' thành '{order.get_status_display()}'"
            if note:
                log_message += f" - Ghi chú: {note}"
            
            messages.success(request, f"Đã cập nhật trạng thái đơn hàng #{order.order_number} thành công!")
        else:
            messages.error(request, "Trạng thái không hợp lệ!")
    
    return redirect('admin_dashboard:orders')