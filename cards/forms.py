from django import forms
from django.core.exceptions import ValidationError
from .models import Card, CardSet

class CardForm(forms.ModelForm):
    """Form for creating and editing cards"""
    
    class Meta:
        model = Card
        fields = [
            'name', 'description', 'card_type', 'rarity', 'card_set', 
            'condition', 'price', 'stock_quantity', 'image',
            'attack', 'defense', 'level'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter card name',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter card description'
            }),
            'card_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'rarity': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'card_set': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'condition': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'attack': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'ATK (Monster cards only)'
            }),
            'defense': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': 'DEF (Monster cards only)'
            }),
            'level': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '12',
                'placeholder': 'Level (Monster cards only)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make monster fields not required by default
        self.fields['attack'].required = False
        self.fields['defense'].required = False
        self.fields['level'].required = False
        
        # Order card sets by name
        self.fields['card_set'].queryset = CardSet.objects.all().order_by('name')

    def clean(self):
        cleaned_data = super().clean()
        card_type = cleaned_data.get('card_type')
        attack = cleaned_data.get('attack')
        defense = cleaned_data.get('defense')
        level = cleaned_data.get('level')

        # Validate monster card fields
        if card_type == 'monster':
            if attack is None:
                raise ValidationError('Attack is required for Monster cards.')
            if defense is None:
                raise ValidationError('Defense is required for Monster cards.')
            if level is None:
                raise ValidationError('Level is required for Monster cards.')
        else:
            # Clear monster fields for non-monster cards
            cleaned_data['attack'] = None
            cleaned_data['defense'] = None
            cleaned_data['level'] = None

        return cleaned_data

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError('Price cannot be negative.')
        return price

    def clean_stock_quantity(self):
        stock_quantity = self.cleaned_data.get('stock_quantity')
        if stock_quantity is not None and stock_quantity < 0:
            raise ValidationError('Stock quantity cannot be negative.')
        return stock_quantity


class CardSetForm(forms.ModelForm):
    """Form for creating and editing card sets"""
    
    class Meta:
        model = CardSet
        fields = ['name', 'code', 'release_date']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter set name',
                'required': True
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter set code (e.g., LOB)',
                'maxlength': '10',
                'required': True
            }),
            'release_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'required': True
            }),
        }

    def clean_code(self):
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
            # Check if code already exists (excluding current instance in edit mode)
            existing = CardSet.objects.filter(code=code)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError('A card set with this code already exists.')
        return code


class BulkCardUploadForm(forms.Form):
    """Form for bulk card upload via CSV"""
    
    csv_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv',
        }),
        help_text='Upload a CSV file with card data. Required columns: name, card_type, rarity, card_set_code, condition, price, stock_quantity'
    )
    
    def clean_csv_file(self):
        csv_file = self.cleaned_data.get('csv_file')
        if csv_file:
            if not csv_file.name.endswith('.csv'):
                raise ValidationError('File must be a CSV file.')
            if csv_file.size > 5 * 1024 * 1024:  # 5MB limit
                raise ValidationError('File size must be less than 5MB.')
        return csv_file