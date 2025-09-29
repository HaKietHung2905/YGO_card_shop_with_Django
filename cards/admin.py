from django.contrib import admin
from .models import Card, CardSet, CartItem, OtherProduct, OrderItem, Order

@admin.register(CardSet)
class CardSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'release_date']
    list_filter = ['release_date']
    search_fields = ['name', 'code']
    ordering = ['-release_date']

@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['name', 'card_type', 'rarity', 'price', 'stock_quantity', 'card_set', 'condition']
    list_filter = ['card_type', 'rarity', 'condition', 'card_set']
    search_fields = ['name', 'description']
    list_editable = ['price', 'stock_quantity']
    ordering = ['name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'card_type', 'image')
        }),
        ('Card Details', {
            'fields': ('rarity', 'card_set', 'condition')
        }),
        ('Monster Stats', {
            'fields': ('attack', 'defense', 'level'),
            'classes': ('collapse',),
            'description': 'Only for Monster cards'
        }),
        ('Inventory', {
            'fields': ('price', 'stock_quantity')
        }),
    )

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'card', 'quantity', 'total_price', 'added_at']
    list_filter = ['added_at', 'card__card_type']
    search_fields = ['user__username', 'card__name']
    readonly_fields = ['total_price']

@admin.register(OtherProduct)
class OtherProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_type', 'brand', 'sku', 'price', 'stock_quantity', 'condition']
    list_filter = ['product_type', 'condition', 'brand']
    search_fields = ['name', 'sku', 'brand']
    list_editable = ['price', 'stock_quantity']
    ordering = ['name']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'payment_status', 'total_amount', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email', 'shipping_full_name']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'created_at', 'updated_at')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax', 'shipping_cost', 'total_amount')
        }),
        ('Shipping Details', {
            'fields': ('shipping_full_name', 'shipping_address', 'shipping_city', 
                      'shipping_state', 'shipping_zip_code', 'shipping_phone')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Notes', {
            'fields': ('order_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'quantity', 'price', 'subtotal', 'created_at']
    list_filter = ['order__status', 'created_at']
    search_fields = ['order__order_number', 'product_name', 'product_sku']
    readonly_fields = ['subtotal', 'created_at']
    ordering = ['-created_at']