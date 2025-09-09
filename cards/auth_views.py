from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages

class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form with additional fields"""
    
    class Meta:
        model = UserCreationForm.Meta.model
        fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')

def signup_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            login(request, user)  # Automatically log in the user
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/signup.html', {'form': form})