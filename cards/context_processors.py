from .models import CardSet, OtherProduct, CartItem
from django.db.models import Sum

def card_sets_processor(request):
    """
    Context processor to make card sets, product types, and cart count available globally.
    """
    card_sets = CardSet.objects.all().order_by('-release_date')
    product_types = OtherProduct.PRODUCT_TYPE_CHOICES
    
    cart_count = 0
    if request.user.is_authenticated:
        # Calculate total items in cart (sum of quantities)
        result = CartItem.objects.filter(user=request.user).aggregate(total=Sum('quantity'))
        cart_count = result['total'] or 0
    
    return {
        'all_card_sets': card_sets,
        'all_product_types': product_types,
        'cart_count': cart_count,
    }
