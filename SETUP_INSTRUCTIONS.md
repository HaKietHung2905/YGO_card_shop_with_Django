# Settings Configuration Required

To complete the dropdown menu implementation, you need to add the context processor to your `settings.py` file.

## Instructions

1. Open `/Users/hung/Work/YGO_card_shop_with_Django/yugioh_shop/settings.py`

2. Find the `TEMPLATES` configuration (it should look like this):

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [...],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # ... other context processors
            ],
        },
    },
]
```

3. Add this line to the `context_processors` list:

```python
'cards.context_processors.card_sets_processor',
```

4. The final configuration should look like:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [...],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cards.context_processors.card_sets_processor',  # ADD THIS LINE
            ],
        },
    },
]
```

5. Save the file and restart your Django development server:

```bash
# Stop the current server (Ctrl+C)
# Then restart it:
python manage.py runserver 8001
```

After completing these steps, the dropdown menu will display all card sets in your navbar!
