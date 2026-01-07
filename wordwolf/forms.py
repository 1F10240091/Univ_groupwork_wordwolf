from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Room, WordSet

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

class SignUpForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'
            field.widget.attrs['placeholder'] = field.label

    class Meta:
        model = User
        fields = ('username', 'email', 'password1')

class UserUpdateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = User
        fields = ('username', 'email')

class RoomForm(forms.ModelForm):
    category = forms.ChoiceField(label='お題カテゴリ')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        categories = WordSet.objects.values_list('category', flat=True).distinct()

        categories = sorted([c for c in categories if c])

        choices = [('all', 'すべて')] + [(c, c) for c in categories]
        self.fields['category'].choices = choices
        
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Room
        fields = ('room_name', 'discussion_time', 'category')
        labels = {
            'room_name': 'ルーム名',
            'discussion_time': '討論時間（分）',
        }
        widgets = {
            'discussion_time': forms.NumberInput(attrs={'min': 1, 'max': 10}),
        }
        help_texts = {
            'discussion_time': '',
            'category': '',
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance