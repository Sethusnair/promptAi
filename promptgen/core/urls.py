from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('home/', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('history/', views.history, name='history'),
    path('favorite/<int:id>/', views.toggle_favorite, name='favorite'),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
]