from django.urls import path
from . import views

app_name = 'wordwolf'
urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('lobby/', views.lobby, name='lobby'),
    path('game/<int:room_id>/', views.game, name='game_room'),
    path('ranking/', views.ranking, name='ranking'),
    path('friends/', views.friend_list, name='friend_list'),
    path('friends/search/', views.search_user, name='search_user'),
    path('friends/approve/<int:request_id>/', views.approve_request, name='approve_request'),
    path('friends/reject/<int:request_id>/', views.reject_request, name='reject_request'),
    path('friends/remove/<int:user_id>/', views.remove_friend, name='remove_friend'),
]