from django.contrib import admin
from .models import Card, CardSet, CartItem

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