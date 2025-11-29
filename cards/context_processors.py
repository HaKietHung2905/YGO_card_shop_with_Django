from .models import CardSet, OtherProduct

def card_sets_processor(request):
    """
    Context processor to make card sets and product types available globally in all templates.
    This allows the navbar to display all card sets and product categories in dropdown menus.
    """
    card_sets = CardSet.objects.all().order_by('-release_date')
    product_types = OtherProduct.PRODUCT_TYPE_CHOICES
    
    return {
        'all_card_sets': card_sets,
        'all_product_types': product_types,
    }
