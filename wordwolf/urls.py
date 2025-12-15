from django.urls import path
from . import views

app_name = 'wordwolf'
urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('lobby/', views.lobby, name='lobby'),
    path('game/', views.game, name='game'),
]