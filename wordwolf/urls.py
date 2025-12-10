from django.urls import path
from . import views

app_name = 'wordwolf'
urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
]