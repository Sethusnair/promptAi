from django.shortcuts import render
from .prompt_engine import detect_task, detect_tone, generate_prompt
from .models import PromptHistory
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

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

@login_required
def home(request):
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
            "tone_conf": round(tone_conf * 100, 2)
        })

    return render(request, "home.html")


from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect

def signup(request):

    if request.method == "POST":
        form = UserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("login")

    else:
        form = UserCreationForm()

    return render(request, "signup.html", {"form": form})


def landing(request):
    return render(request, "landing.html")

def how_it_works(request):
    return render(request,"how_it_works.html")