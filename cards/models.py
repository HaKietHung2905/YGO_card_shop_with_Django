from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

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
        return reverse('card_detail', kwargs={'pk': self.pk})
    
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