from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('history/', views.history, name='history'),
    path('favorite/<int:id>/', views.toggle_favorite, name='favorite'),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("delete/<int:id>/", views.delete_prompt, name="delete_prompt"),
    path("continue-chat/", views.continue_chat, name="continue_chat"),
]