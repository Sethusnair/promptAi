from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from .models import PromptHistory

from .forms import SignupForm
from .prompt_engine import detect_task, detect_tone
from .models import PromptHistory, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

def get_smart_questions(user_input):

    text = user_input.lower()

    # 🌍 TRAVEL / TRIP
    if any(k in text for k in ["trip", "travel", "vacation", "tour"]):
        return [
            "Where do you want to go?",
            "What is your budget?",
            "How many days will the trip be?"
        ]

    # 📄 RESUME / CV
    elif any(k in text for k in ["resume", "cv", "job", "portfolio"]):
        return [
            "What is your profession or role?",
            "How many years of experience do you have?",
            "What are your key skills or achievements?"
        ]

    # 💻 CODE / PROGRAMMING
    elif any(k in text for k in ["code", "program", "api", "backend", "frontend", "app"]):
        return [
            "What technology or language should be used?",
            "What is the main functionality?",
            "Any specific requirements or constraints?"
        ]

    # ✍️ CONTENT / WRITING
    elif any(k in text for k in ["blog", "article", "post", "content", "story"]):
        return [
            "What is the topic?",
            "Who is the target audience?",
            "What tone or style do you prefer?"
        ]

    # 📊 BUSINESS / PLAN
    elif any(k in text for k in ["business", "plan", "startup", "idea"]):
        return [
            "What is the business idea?",
            "Who is the target market?",
            "What is the main goal or outcome?"
        ]

    # 📚 STUDY / LEARNING
    elif any(k in text for k in ["study", "learn", "course", "roadmap"]):
        return [
            "What do you want to learn?",
            "What is your current level?",
            "What is your goal or timeline?"
        ]

    # 🎨 DESIGN
    elif any(k in text for k in ["design", "ui", "ux", "logo"]):
        return [
            "What type of design do you need?",
            "What style or theme do you prefer?",
            "Any specific colors or requirements?"
        ]

    # 🔧 DEFAULT
    else:
        return [
            "What is your goal?",
            "Who is this for?",
            "Any specific requirements?"
        ]

def extract_questions(text):
    lines = text.split("\n")
    questions = []

    for l in lines:
        l = l.strip()

        # accept if it LOOKS like a question
        if "?" in l or l.lower().startswith(("what", "where", "how", "why", "who")):
            
            # clean numbering
            if "." in l:
                l = l.split(".", 1)[-1].strip()

            # ensure it ends with ?
            if not l.endswith("?"):
                l += "?"

            questions.append(l)

    return questions[:3]

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

import ollama


@login_required
def home(request):

    profile = UserProfile.objects.get(user=request.user)

    if "chat_history" not in request.session:
        request.session["chat_history"] = []

    if "questions" not in request.session:
        request.session["questions"] = None

    chat_history = request.session["chat_history"]

    if request.method == "POST":

        user_input = request.POST.get("input_text")
        answers = request.POST.getlist("answers")

        # =========================
        # FINAL STAGE → PROMPT GENERATION
        # =========================
        if answers:

            topic = request.session.get("topic")

            qa_text = ""
            for q, a in zip(get_smart_questions(topic), answers):
                qa_text += f"{q} {a}. "

            # 🔥 MINIMAL PROMPT (IMPORTANT)
#             final_prompt = f"""
# Topic: {topic}
# Details: {qa_text}

# Write ONE detailed and specific prompt starting with "Create".

# The prompt must include:
# - clear goal
# - important details from input
# - key components (steps, features, or structure)

# IMP: THE PROMPT SHOULD ME LARGRE,NOT A SINGLE LINE OR DOUBLE LINE IT SHOULD BE VERY LARGE PROMPT.

# CREATE DEATILED PROMPT MORE DESCRIPTIVE PROMPT.
# """
            final_prompt = f"""
User request: {topic}

User details:
{qa_text}

Write a highly detailed and descriptive prompt.

The prompt should:
- clearly define the goal
- include all user details
- mention important sections/structure
- be suitable for another AI to generate full output

Start with "Create".
"""

            response = ollama.chat(
                model="tinyllama",
                messages=[
                    {
                        "role": "system",
                        "content": "Output only one sentence starting with 'Create'. No explanation."
                    },
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ],
                options={"temperature": 0}
            )

            ai_reply = response["message"]["content"].strip()

            # 🔥 HARD VALIDATION (MOST IMPORTANT)
            ai_reply = ai_reply.replace("\n", " ").strip()

            # force correct format
            if not ai_reply.lower().startswith("create"):
                ai_reply = f"Create a detailed {topic} based on {qa_text}."

            # remove junk
            bad_words = ["here", "sure", "example", "assistant", "user:"]
            for b in bad_words:
                ai_reply = ai_reply.replace(b, "")

            # keep only one sentence
            # if "." in ai_reply:
            #     ai_reply = ai_reply.split(".")[0] + "."

            # clean chat
            request.session["chat_history"] = [
                {"role": "user", "content": topic},
                {"role": "assistant", "content": ai_reply}
            ]

            PromptHistory.objects.create(
                user=request.user,
                user_input=topic,
                task_type="custom",
                tone="custom",
                generated_prompt=ai_reply
            )

            request.session["questions"] = None

            return redirect("home")

        # =========================
        # QUESTION STAGE
        # =========================

        request.session["chat_history"] = []

        # 🔥 MINIMAL QUESTION PROMPT
        system_prompt = f"""
Ask EXACTLY 3 short and simple questions.

User request: {user_input}

Rules:
- Only questions
- Each must end with '?'
- No explanation
- No extra text

Example:
Where do you want to go?
What is your budget?
How many days?
"""

        response = ollama.chat(
            model="tinyllama",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            options={"temperature": 0}
        )

        ai_reply = response["message"]["content"]


        questions = extract_questions(ai_reply)

        questions = get_smart_questions(user_input)

        request.session["questions"] = questions
        request.session["topic"] = user_input

        request.session["chat_history"] = [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": "\n".join(questions)}
        ]

        return redirect("home")

    return render(request, "home.html", {
        "profile": profile,
        "chat_history": chat_history
    })
        # 🔥 STRICT QUESTION EXTRACTION

def clean_output(text, stage):

    text = text.strip()

    if stage == "question":
        lines = text.split("\n")

        # Keep only bullet questions
        lines = [l for l in lines if l.strip().startswith("-")]

        return "\n".join(lines[:7])  # limit questions

    elif stage == "final":
        # Remove unwanted words
        banned = ["sorry", "tips", "guidance", "i am", "here are", "good luck"]
        for b in banned:
            text = text.replace(b, "")

        return text.strip()

    return text


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

def continue_chat(request):
    if request.method == "POST":

        reply = request.POST.get("reply_text")

        chat_history = request.session.get("chat_history", [])

        chat_history.append({"role": "user", "content": reply})

        response = ollama.chat(
            model="tinyllama",
            messages=chat_history
        )

        ai_reply = response["message"]["content"]

        request.session["chat_history"] = [
        {"role": "user", "content": topic},
        {"role": "assistant", "content": ai_reply}
]

        request.session["chat_history"] = chat_history

        return redirect("home")

