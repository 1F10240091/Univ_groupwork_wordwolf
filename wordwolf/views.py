from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.db.models import Q
from .forms import SignUpForm
from .models import Room

class SignUpView(generic.CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/signup.html'

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
