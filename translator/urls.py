from django.urls import path
from .views import ChatAPI, home

urlpatterns = [
    path('', home, name='home'),
    path('chat/', ChatAPI.as_view()),
]