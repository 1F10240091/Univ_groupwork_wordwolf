from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, UserUpdateForm
from .models import Room, User

class SignUpView(generic.CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

@login_required
def profile(request):
    user = request.user
    total_games = user.win_num + user.lose_num
    win_rate = 0
    if total_games > 0:
        win_rate = (user.win_num / total_games) * 100
    
    context = {
        'user': user,
        'total_games': total_games,
        'win_rate': win_rate,
    }
    return render(request, 'wordwolf/profile.html', context)

@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('wordwolf:profile')
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, 'wordwolf/profile_edit.html', {'form': form})

def home(request):
    if request.user.is_authenticated:
        return redirect('wordwolf:lobby')
    return render(request, 'wordwolf/home.html', {})

def lobby(request):
    query = request.GET.get('q')
    rooms = Room.objects.filter(status=Room.Status.WAITING).order_by('-created_at')
    
    if query:
        rooms = rooms.filter(room_name__icontains=query)
    
    return render(request, 'wordwolf/lobby.html', {
        'rooms': rooms,
        'query': query,
    })

def game(request):
    return render(request, 'wordwolf/game.html', {})

@login_required
def friend_list(request):
    context = {
        'friend_requests': [],
        'friends': [],
    }
    return render(request, 'wordwolf/friend.html', context)

@login_required
def search_user(request):
    return redirect('wordwolf:friend_list')

@login_required
def approve_request(request, request_id):
    return redirect('wordwolf:friend_list')

@login_required
def reject_request(request, request_id):
    return redirect('wordwolf:friend_list')

@login_required
def remove_friend(request, user_id):
    return redirect('wordwolf:friend_list')

def ranking(request):
    top_users = User.objects.order_by('-win_num')[:10]
    ranking_list = []
    for user in top_users:
        ranking_list.append({
            'user': user,
            'score': user.win_num,
            'games_played': user.win_num + user.lose_num
        })
    return render(request, 'wordwolf/ranking.html', {'ranking_list': ranking_list})