from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from .models import PromptHistory

from .forms import SignupForm
from .prompt_engine import detect_task, detect_tone, generate_prompt
from .models import PromptHistory, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

@login_required
def toggle_favorite(request, id):
    prompt = PromptHistory.objects.get(id=id, user=request.user)
    prompt.is_favorite = not prompt.is_favorite
    prompt.save()
    return redirect('history')

@login_required
def history(request):
    prompts = PromptHistory.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "history.html", {"prompts": prompts})

from .models import UserProfile

@login_required
def home(request):

    profile = UserProfile.objects.get(user=request.user)

    if request.method == "POST":

        user_input = request.POST.get("input_text")

        task, task_conf = detect_task(user_input)
        tone, tone_conf = detect_tone(user_input)

        final_prompt = generate_prompt(user_input, task, tone)

        PromptHistory.objects.create(
            user=request.user,
            user_input=user_input,
            task_type=task,
            tone=tone,
            generated_prompt=final_prompt
        )

        return render(request, "result.html", {
            "prompt": final_prompt,
            "task": task,
            "tone": tone,
            "task_conf": round(task_conf * 100, 2),
            "tone_conf": round(tone_conf * 100, 2),
            "profile": profile
        })

    return render(request, "home.html", {
        "profile": profile
    })


from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

def signup(request):

    if request.method == "POST":

        form = SignupForm(request.POST)

        if form.is_valid():

            user = form.save()

            UserProfile.objects.create(
                user=user,
                profession=form.cleaned_data["profession"],
                current_role=form.cleaned_data["current_role"],
                experience=form.cleaned_data["experience"],
                interests=form.cleaned_data["interests"]
            )

            login(request, user)

            return redirect("home")

    else:
        form = SignupForm()

    return render(request, "signup.html", {"form": form})


def landing(request):
    return render(request, "landing.html")

def how_it_works(request):
    return render(request,"how_it_works.html")

def delete_prompt(request, id):

    prompt = get_object_or_404(PromptHistory, id=id, user=request.user)

    if request.method == "POST":
        prompt.delete()

    return redirect("history")