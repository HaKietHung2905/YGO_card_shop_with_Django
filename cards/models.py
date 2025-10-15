from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import models
import uuid  

class CardSet(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)
    release_date = models.DateField()
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-release_date']

class Card(models.Model):
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('super_rare', 'Super Rare'),
        ('ultra_rare', 'Ultra Rare'),
        ('secret_rare', 'Secret Rare'),
        ('ghost_rare', 'Ghost Rare'),
    ]
    
    CONDITION_CHOICES = [
        ('mint', 'Mint'),
        ('near_mint', 'Near Mint'),
        ('lightly_played', 'Lightly Played'),
        ('moderately_played', 'Moderately Played'),
        ('heavily_played', 'Heavily Played'),
        ('damaged', 'Damaged'),
    ]
    
    CARD_TYPE_CHOICES = [
        ('monster', 'Monster'),
        ('spell', 'Spell'),
        ('trap', 'Trap'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    card_type = models.CharField(max_length=20, choices=CARD_TYPE_CHOICES)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES)
    card_set = models.ForeignKey(CardSet, on_delete=models.CASCADE)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='cards/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Monster-specific fields (optional)
    attack = models.IntegerField(null=True, blank=True)
    defense = models.IntegerField(null=True, blank=True)
    level = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.rarity})"
    
    def get_absolute_url(self):
        return reverse('card_detail', kwargs={'pk': self.pk})  # Uses card_detail URL name
    
    @property
    def is_in_stock(self):
        return self.stock_quantity > 0
    
    class Meta:
        ordering = ['name']

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.card.name} ({self.quantity})"
    
    @property
    def total_price(self):
        return self.card.price * self.quantity
    
    class Meta:
        unique_together = ('user', 'card')

class OtherProduct(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('deck_box', 'Deck Box'),
        ('sleeves', 'Card Sleeves'),
        ('playmat', 'Playmat'),
        ('booster_box', 'Booster Box'),
        ('starter_deck', 'Starter Deck'),
        ('structure_deck', 'Structure Deck'),
        ('tin', 'Collector Tin'),
        ('accessory', 'Gaming Accessory'),
        ('merchandise', 'Merchandise'),
    ]
    
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('opened', 'Opened'),
        ('used', 'Used'),
        ('damaged', 'Damaged'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    brand = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='other_products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Optional fields for specific product types
    dimensions = models.CharField(max_length=100, blank=True)  # For deck boxes, playmats
    material = models.CharField(max_length=100, blank=True)   # For sleeves, accessories
    quantity_per_pack = models.PositiveIntegerField(null=True, blank=True)  # For sleeves
    
    def __str__(self):
        return f"{self.name} ({self.get_product_type_display()})"
    
    @property
    def is_in_stock(self):
        return self.stock_quantity > 0
    
    class Meta:
        ordering = ['name'] 
    

class Order(models.Model):
    """Order model to track customer purchases"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('paypal', 'PayPal'),
        ('bank_transfer', 'Bank Transfer'),
        ('cash_on_delivery', 'Cash on Delivery'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Pricing
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Shipping Information
    shipping_full_name = models.CharField(max_length=200)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_zip_code = models.CharField(max_length=20)
    shipping_phone = models.CharField(max_length=20)
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, default='unpaid')
    
    # Notes
    order_notes = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_order_number():
        """Generate unique order number"""
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"
    
    @property
    def total_items(self):
        """Get total number of items in order"""
        return sum(item.quantity for item in self.items.all())


class OrderItem(models.Model):
    """Individual items in an order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    
    # Product reference (either card or other product)
    card = models.ForeignKey('Card', on_delete=models.SET_NULL, null=True, blank=True)
    other_product = models.ForeignKey('OtherProduct', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Store product details at time of purchase
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=100, blank=True, null=True)
    
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        # Calculate subtotal
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)
    
    @property
    def get_product(self):
        """Return the actual product (card or other_product)"""
        return self.card if self.card else self.other_product
    

class Tournament(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    FORMAT_CHOICES = [
        ('standard', 'Standard'),
        ('traditional', 'Traditional'),
        ('goat', 'GOAT Format'),
        ('edison', 'Edison Format'),
        ('draft', 'Draft'),
        ('sealed', 'Sealed'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    format = models.CharField(max_length=50, choices=FORMAT_CHOICES, default='standard')
    max_participants = models.IntegerField(null=True, blank=True, help_text="Leave blank for unlimited")
    entry_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    prize_pool = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    
    # Relationships
    participants = models.ManyToManyField(User, related_name='tournaments', blank=True)
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='organized_tournaments')
    
    # Additional info
    rules = models.TextField(blank=True, null=True)
    prize_structure = models.TextField(blank=True, null=True, help_text="1st: $100, 2nd: $50, etc.")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.date}"
    
    @property
    def is_full(self):
        if self.max_participants:
            return self.participants.count() >= self.max_participants
        return False
    
    @property
    def spots_remaining(self):
        if self.max_participants:
            return self.max_participants - self.participants.count()
        return None
    
    @property
    def participants_count(self):
        return self.participants.count()
    
    def can_register(self, user):
        """Check if a user can register for this tournament"""
        if self.status != 'upcoming':
            return False
        if self.is_full:
            return False
        if user in self.participants.all():
            return False
        return True
    
    class Meta:
        ordering = ['-date', '-start_time']
        verbose_name = 'Tournament'
        verbose_name_plural = 'Tournaments'

class SiteSettings(models.Model):
    # General Settings
    site_name = models.CharField(max_length=200, default='Yu-Gi-Oh Card Shop')
    maintenance_mode = models.BooleanField(default=False)
    allow_registration = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    theme_mode = models.CharField(max_length=20, default='light', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto')
    ])
    
    # Shop Settings
    currency = models.CharField(max_length=10, default='VND')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    low_stock_threshold = models.IntegerField(default=5)
    
    # Tournament Settings
    auto_approve_registrations = models.BooleanField(default=True)
    default_max_participants = models.IntegerField(default=32)
    registration_deadline_hours = models.IntegerField(default=24)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return f"Settings - {self.site_name}"
    
    @classmethod
    def get_settings(cls):
        """Get or create settings instance"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings