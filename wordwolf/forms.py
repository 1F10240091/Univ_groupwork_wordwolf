from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1')

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')