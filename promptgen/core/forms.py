from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class SignupForm(UserCreationForm):

    profession = forms.CharField(max_length=100)
    current_role = forms.CharField(max_length=150)
    experience = forms.IntegerField()
    interests = forms.CharField(max_length=200)

    class Meta:
        model = User
        fields = [
            "username",
            "password1",
            "password2",
            "profession",
            "current_role",
            "experience",
            "interests"
        ]