from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Room, WordSet

class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'password1')

class UserUpdateForm(forms.ModelForm):
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