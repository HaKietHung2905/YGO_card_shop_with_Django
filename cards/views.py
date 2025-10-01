# Enhanced home view to include other products and better data loading
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import QueryDict
from .models import Card, CardSet, CartItem, OtherProduct, Order, OrderItem
from django.db import transaction
from decimal import Decimal

def home(request):
    """Enhanced homepage view with featured cards and other products"""
    # Get featured cards (in stock only)
    featured_cards = Card.objects.filter(stock_quantity__gt=0).select_related('card_set')[:8]
    
    # Get latest card sets
    latest_sets = CardSet.objects.all().order_by('-release_date')[:4]
    
    # Get featured accessories/other products (optional)
    featured_accessories = OtherProduct.objects.filter(
        stock_quantity__gt=0, 
        is_active=True
    ).order_by('-created_at')[:4]
    
    # Get some statistics for the homepage
    total_cards_available = Card.objects.filter(stock_quantity__gt=0).count()
    total_accessories = OtherProduct.objects.filter(stock_quantity__gt=0, is_active=True).count()
    
    context = {
        'featured_cards': featured_cards,
        'latest_sets': latest_sets,
        'featured_accessories': featured_accessories,
        'total_cards_available': total_cards_available,
        'total_accessories': total_accessories,
    }
    return render(request, 'home.html', context)

def other_products_list(request):
    """Public view for browsing other products (accessories, etc.)"""
    products = OtherProduct.objects.filter(is_active=True, stock_quantity__gt=0)
    
    # Search functionality
    query = request.GET.get('q', '')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(brand__icontains=query)
        )
    
    # Filter by product type
    product_type = request.GET.get('type', '')
    if product_type:
        products = products.filter(product_type=product_type)
    
    # Filter by brand
    brand = request.GET.get('brand', '')
    if brand:
        products = products.filter(brand=brand)
    
    # Price range filter
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Ordering
    ordering = request.GET.get('ordering', '')
    if ordering:
        products = products.order_by(ordering)
    else:
        products = products.order_by('name')
    
    # Pagination
    paginator = Paginator(products, 12)  # 12 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options for the template
    product_types = OtherProduct.objects.values_list('product_type', flat=True).distinct()
    brands = OtherProduct.objects.exclude(brand='').values_list('brand', flat=True).distinct()
    
    # Build query parameters for pagination links
    query_params = QueryDict(mutable=True)
    for key, value in request.GET.items():
        if key != 'page' and value:
            query_params[key] = value
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'query': query,
        'selected_type': product_type,
        'selected_brand': brand,
        'min_price': min_price,
        'max_price': max_price,
        'product_types': product_types,
        'brands': brands,
        'product_type_choices': OtherProduct.PRODUCT_TYPE_CHOICES,
        'query_params': query_params.urlencode(),
    }
    return render(request, 'cards/other_products_list.html', context)

def other_product_detail(request, pk):
    """Display individual other product details"""
    product = get_object_or_404(OtherProduct, pk=pk, is_active=True)
    
    # Get related products (same type or brand)
    related_products = OtherProduct.objects.filter(
        Q(product_type=product.product_type) | Q(brand=product.brand),
        is_active=True,
        stock_quantity__gt=0
    ).exclude(pk=product.pk)[:4]
    
    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'cards/other_product_detail.html', context)

@login_required
def add_other_product_to_cart(request, pk):
    """Add other product to user's cart (you'll need to extend CartItem model)"""
    product = get_object_or_404(OtherProduct, pk=pk, is_active=True)
    
    if product.stock_quantity <= 0:
        messages.error(request, 'This product is out of stock.')
        return redirect('other_product_detail', pk=pk)
    
    # Note: You might need to modify CartItem model to support both cards and other products
    # For now, this assumes you have a way to handle other products in the cart
    
    messages.success(request, f'Added {product.name} to cart.')
    
    # Redirect back to the previous page or product detail
    next_url = request.META.get('HTTP_REFERER', None)
    if next_url and 'product' in next_url:
        return redirect(next_url)
    return redirect('other_product_detail', pk=pk)

def card_list(request):
    """Display all cards with filtering and search"""
    cards = Card.objects.filter(stock_quantity__gt=0).select_related('card_set')
    
    # Search functionality
    query = request.GET.get('q', '')
    if query:
        cards = cards.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query)
        )
    
    # Filter by card type
    card_type = request.GET.get('type', '')
    if card_type:
        cards = cards.filter(card_type=card_type)
    
    # Filter by rarity
    rarity = request.GET.get('rarity', '')
    if rarity:
        cards = cards.filter(rarity=rarity)
    
    # Filter by card set
    card_set = request.GET.get('set', '')
    if card_set:
        cards = cards.filter(card_set__id=card_set)
    
    # Price range filter
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    if min_price:
        cards = cards.filter(price__gte=min_price)
    if max_price:
        cards = cards.filter(price__lte=max_price)
    
    # Ordering
    ordering = request.GET.get('ordering', '')
    if ordering:
        cards = cards.order_by(ordering)
    else:
        cards = cards.order_by('name')
    
    # Pagination
    paginator = Paginator(cards, 12)  # 12 cards per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    card_sets = CardSet.objects.all()
    
    # Build query parameters for pagination links
    query_params = QueryDict(mutable=True)
    for key, value in request.GET.items():
        if key != 'page' and value:
            query_params[key] = value
    
    context = {
        'page_obj': page_obj,
        'card_sets': card_sets,
        'query': query,
        'selected_type': card_type,
        'selected_rarity': rarity,
        'selected_set': card_set,
        'min_price': min_price,
        'max_price': max_price,
        'card_type_choices': Card.CARD_TYPE_CHOICES,
        'rarity_choices': Card.RARITY_CHOICES,
        'query_params': query_params.urlencode(),
    }
    return render(request, 'cards/card_list.html', context)

def card_detail(request, pk):
    """Display individual card details"""
    card = get_object_or_404(Card, pk=pk)
    related_cards = Card.objects.filter(
        card_set=card.card_set,
        stock_quantity__gt=0
    ).exclude(pk=card.pk)[:4]
    
    context = {
        'card': card,
        'related_cards': related_cards,
    }
    return render(request, 'cards/card_detail.html', context)

@login_required
def add_to_cart(request, pk):
    """Add card to user's cart"""
    card = get_object_or_404(Card, pk=pk)
    
    if card.stock_quantity <= 0:
        messages.error(request, 'This card is out of stock.')
        return redirect('card_detail', pk=pk)
    
    cart_item, created = CartItem.objects.get_or_create(
        user=request.user,
        card=card,
        defaults={'quantity': 1}
    )
    
    print(f"DEBUG: Created new item: {created}")
    print(f"DEBUG: Cart item ID: {cart_item.id}")
    print(f"DEBUG: Quantity: {cart_item.quantity}")

    if not created:
        if cart_item.quantity >= card.stock_quantity:
            messages.warning(request, f'Maximum stock ({card.stock_quantity}) reached for {card.name}.')
        else:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'Increased {card.name} quantity in cart.')
    else:
        messages.success(request, f'Added {card.name} to cart.')
    
    # Redirect back to the previous page or card detail
    next_url = request.META.get('HTTP_REFERER', None)
    if next_url and 'card' in next_url:
        return redirect(next_url)
    return redirect('card_detail', pk=pk)

@login_required
def cart(request):
    """Display user's cart"""
    cart_items = CartItem.objects.filter(user=request.user).select_related('card', 'card__card_set')
    total = sum(item.total_price for item in cart_items)
    
    # Debug
    print(f"DEBUG CART VIEW: Found {cart_items.count()} items")
    for item in cart_items:
        print(f"  - {item.card.name} x{item.quantity}")
    
    context = {
        'cart_items': cart_items,
        'total': total,
    }
    return render(request, 'cards/cart.html', context)

@login_required
def remove_from_cart(request, pk):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)
    card_name = cart_item.card.name
    cart_item.delete()
    messages.success(request, f'Removed {card_name} from cart.')
    return redirect('cart')

@login_required
def update_cart_quantity(request, pk):
    """Update cart item quantity"""
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, pk=pk, user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, f'Removed {cart_item.card.name} from cart.')
        elif quantity > cart_item.card.stock_quantity:
            messages.error(request, f'Only {cart_item.card.stock_quantity} units available.')
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f'Updated {cart_item.card.name} quantity.')
    
    return redirect('cart')

@login_required
def checkout(request):
    """Display checkout page with cart items and shipping form"""
    cart_items = CartItem.objects.filter(user=request.user).select_related('card', 'card__card_set')
    
    if not cart_items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('cart')
    
    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    tax_rate = Decimal('0.085')  # 8.5% tax
    tax = subtotal * tax_rate
    shipping = Decimal('0.00')  # Free shipping
    total = subtotal + tax + shipping
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'shipping': shipping,
        'total': total,
    }
    return render(request, 'cards/checkout.html', context)


@login_required
@transaction.atomic
def process_checkout(request):
    """Process the checkout and create order"""
    if request.method != 'POST':
        return redirect('checkout')
    
    # Get cart items
    cart_items = CartItem.objects.filter(user=request.user).select_related('card')
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')
    
    # Validate stock availability
    for item in cart_items:
        product = item.card
        if product.stock_quantity < item.quantity:
            messages.error(request, f'Insufficient stock for {product.name}. Available: {product.stock_quantity}')
            return redirect('cart')
    
    # Calculate totals
    subtotal = sum(item.total_price for item in cart_items)
    tax_rate = Decimal('0.085')
    tax = subtotal * tax_rate
    shipping = Decimal('0.00')
    total = subtotal + tax + shipping
    
    try:
        # Create order
        order = Order.objects.create(
            user=request.user,
            subtotal=subtotal,
            tax=tax,
            shipping_cost=shipping,
            total_amount=total,
            shipping_full_name=request.POST.get('full_name'),
            shipping_address=request.POST.get('address'),
            shipping_city=request.POST.get('city'),
            shipping_state=request.POST.get('state'),
            shipping_zip_code=request.POST.get('zip_code'),
            shipping_phone=request.POST.get('phone'),
            payment_method=request.POST.get('payment_method', 'credit_card'),
            order_notes=request.POST.get('order_notes', ''),
        )
        
        # Create order items and update stock
        for item in cart_items:
            product = item.card
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                card=product,
                product_name=product.name,
                product_sku='',  # Cards don't have SKU
                quantity=item.quantity,
                price=product.price,
                subtotal=item.total_price
            )
            
            # Update stock
            product.stock_quantity -= item.quantity
            product.save()
        
        # Mark order as confirmed and paid
        order.status = 'confirmed'
        order.payment_status = 'paid'
        order.save()
        
        # Clear cart
        cart_items.delete()
        
        messages.success(request, f'Order {order.order_number} placed successfully!')
        return redirect('order_confirmation', order_id=order.id)
        
    except Exception as e:
        messages.error(request, f'Error processing order: {str(e)}')
        return redirect('checkout')


@login_required
def order_confirmation(request, order_id):
    """Display order confirmation page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'cards/orders/order_confirmation.html', context)


@login_required
def my_orders(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items')
    
    context = {
        'orders': orders,
    }
    return render(request, 'cards/orders/my_orders.html', context)


@login_required
def order_detail(request, order_id):
    """Display detailed view of a specific order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'cards/orders/order_detail.html', context)


@login_required
def cancel_order(request, order_id):
    """Cancel an order (only if status is pending or confirmed)"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status in ['pending', 'confirmed']:
        # Restore stock
        for item in order.items.all():
            if item.card:
                item.card.stock_quantity += item.quantity
                item.card.save()
            elif item.other_product:
                item.other_product.stock_quantity += item.quantity
                item.other_product.save()
        
        order.status = 'cancelled'
        order.save()
        messages.success(request, f'Order {order.order_number} has been cancelled.')
    else:
        messages.error(request, 'This order cannot be cancelled.')
    
    return redirect('order_detail', order_id=order_id)