from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, UserUpdateForm, RoomForm
from .models import Room, User, Member, FriendRequest

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

@login_required
def game(request, room_id):
    # 指定されたroom_idで、かつ自分がメンバーであるルームを探す
    member = get_object_or_404(Member, user=request.user, room__id=room_id)
    
    # ルームの状態チェック（終了していたら入れないなど）
    # ただし、結果表示画面などで使うかもしれないので、とりあえずステータスチェックは緩和するか要検討
    # ここでは PLAYING, VOTING, FINISHED すべて許可するが、WAITINGならロビー(ルーム詳細)へ戻す
    if member.room.status == Room.Status.WAITING:
        return redirect('wordwolf:room_detail', room_id=room_id)
    
    return render(request, 'wordwolf/game.html', {
        'room': member.room,
    })

@login_required
def friend_list(request):
    friend_requests = FriendRequest.objects.filter(to_user=request.user)
    friends = request.user.friends.all()

    context = {
        'friend_requests': friend_requests,
        'friends': friends,
    }
    return render(request, 'wordwolf/friend.html', context)
@login_required
def search_user(request):
    query = request.GET.get('query')
    search_results = []
    
    if query:
        search_results = User.objects.filter(
            username__icontains=query
        ).exclude(id=request.user.id)
    
    return render(request, 'wordwolf/search_results.html', {
        'users': search_results, 
        'query': query
    })

@login_required
def send_request(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        
        if target_user not in request.user.friends.all():
            existing_request = FriendRequest.objects.filter(
                from_user=request.user, 
                to_user=target_user
            ).exists()
            
            reverse_request = FriendRequest.objects.filter(
                from_user=target_user,
                to_user=request.user
            ).exists()

            if not existing_request and not reverse_request:
                FriendRequest.objects.create(from_user=request.user, to_user=target_user)

    return redirect('wordwolf:friend_list')

@login_required
def approve_request(request, request_id):
    if request.method == 'POST':
        friend_request = get_object_or_404(FriendRequest, id=request_id)
        
        if friend_request.to_user == request.user:
            request.user.friends.add(friend_request.from_user)
            
            friend_request.delete()
            
    return redirect('wordwolf:friend_list')

@login_required
def reject_request(request, request_id):
    if request.method == 'POST':
        friend_request = get_object_or_404(FriendRequest, id=request_id)
        
        if friend_request.to_user == request.user:
            friend_request.delete()
    return redirect('wordwolf:friend_list')

@login_required
def remove_friend(request, user_id):
    if request.method == 'POST':
        friend_to_remove = get_object_or_404(User, id=user_id)
        
        request.user.friends.remove(friend_to_remove)
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

@login_required
def create_game(request):
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():

            room = form.save(commit=False)

            room.host = request.user

            room.save()

            Member.objects.create(user=request.user, room=room)
            return redirect('wordwolf:room_detail', room_id=room.id)
    else:
        form = RoomForm()
    return render(request, 'wordwolf/create_game.html', {'form': form})

@login_required
def room_detail(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    # メンバーかどうか確認し、メンバーでなければ追加
    if not Member.objects.filter(user=request.user, room=room).exists():
        Member.objects.create(user=request.user, room=room)
    
    members = Member.objects.filter(room=room)
    return render(request, 'wordwolf/room_detail.html', {'room': room, 'members': members})
