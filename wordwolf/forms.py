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
        # DBからカテゴリ一覧を取得（重複なし）
        categories = WordSet.objects.values_list('category', flat=True).distinct()
        # 空文字を除外してソート
        categories = sorted([c for c in categories if c])
        
        # 選択肢を生成（'all' は固定）
        choices = [('all', 'すべて')] + [(c, c) for c in categories]
        self.fields['category'].choices = choices

    class Meta:
        model = Room
        fields = ('room_name', 'max_user_num', 'discussion_time', 'category')
        labels = {
            'room_name': 'ルーム名',
            'max_user_num': '最大人数',
            'discussion_time': '討論時間（分）',
        }
        widgets = {
            'discussion_time': forms.NumberInput(attrs={'min': 1, 'max': 10}),
            'max_user_num': forms.NumberInput(attrs={'min': 2, 'max': 10}),
        }
        help_texts = {
            'discussion_time': '',
            'category': '',
        }
