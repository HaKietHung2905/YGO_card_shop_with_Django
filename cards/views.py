from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import QueryDict
from .models import Card, CardSet, CartItem

def home(request):
    """Homepage view"""
    featured_cards = Card.objects.filter(stock_quantity__gt=0)[:8]
    latest_sets = CardSet.objects.all()[:4]
    
    context = {
        'featured_cards': featured_cards,
        'latest_sets': latest_sets,
    }
    return render(request, 'cards/home.html', context)

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
    
    if not created:
        # Check if adding one more would exceed stock
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
def update_cart(request):
    """Update cart item quantities"""
    if request.method == 'POST':
        updated_items = 0
        for item_id, quantity in request.POST.items():
            if item_id.startswith('quantity_'):
                cart_item_id = item_id.replace('quantity_', '')
                try:
                    cart_item = CartItem.objects.get(id=cart_item_id, user=request.user)
                    new_quantity = int(quantity)
                    
                    if new_quantity > 0:
                        # Check stock limits
                        if new_quantity <= cart_item.card.stock_quantity:
                            cart_item.quantity = new_quantity
                            cart_item.save()
                            updated_items += 1
                        else:
                            messages.warning(request, 
                                f'Quantity for {cart_item.card.name} limited to available stock ({cart_item.card.stock_quantity}).')
                            cart_item.quantity = cart_item.card.stock_quantity
                            cart_item.save()
                    else:
                        cart_item.delete()
                        updated_items += 1
                        
                except (CartItem.DoesNotExist, ValueError):
                    continue
        
        if updated_items > 0:
            messages.success(request, 'Cart updated successfully.')
        else:
            messages.info(request, 'No changes were made to your cart.')
    
    return redirect('cart')