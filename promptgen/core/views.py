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

def extract_questions(text):
    lines = text.split("\n")
    questions = []

    for l in lines:
        l = l.strip()

        if "?" not in l:
            continue

        # remove numbering like "Question 1."
        if "." in l:
            l = l.split(".",1)[1].strip()

        questions.append(l)

    return questions[:5]

@login_required
def home(request):

    profile = UserProfile.objects.get(user=request.user)

    # INIT SESSION
    if "chat_history" not in request.session:
        request.session["chat_history"] = []

    if "stage" not in request.session:
        request.session["stage"] = "question"

    if "questions" not in request.session:
        request.session["questions"] = None

    chat_history = request.session["chat_history"]

    if request.method == "POST":

        user_input = request.POST.get("input_text")
        answers = request.POST.getlist("answers")

        # 🔥 =========================
        # FINAL STAGE
        # 🔥 =========================
        if answers:

            request.session["stage"] = "final"

            topic = request.session.get("topic")
            questions = request.session.get("questions")

            # Format Q&A
            qa_text = ""
            for i, (q, a) in enumerate(zip(questions, answers), start=1):
                qa_text += f"Answer {i}: {a}\n"

            final_prompt = f"""
User wants to create: {topic}

User answers:
{qa_text}

Using ONLY these answers, generate ONE clean and professional AI prompt.

Do NOT:
- Repeat the questions
- Add explanation
- Add "Sure" or assistant tone

ONLY output the final prompt.
"""

            response = ollama.chat(
                model="tinyllama",
                messages=[
                    {
                        "role": "system",
    "content": """
You generate only final prompts.

Strict rules:
- Do NOT repeat questions
- Do NOT explain anything
- Do NOT say "Sure"
- Do NOT behave like assistant
- Use ONLY the provided answers

Output ONLY one clean prompt.
"""
                    },
                    {
                        "role": "user",
                        "content": final_prompt
                    }
                ],
                options={"temperature": 0.2}
            )

            ai_reply = response["message"]["content"].strip()
    

            # Save to chat
            chat_history.append({"role": "assistant", "content": ai_reply})
            request.session["chat_history"] = chat_history

            # Save to DB
            PromptHistory.objects.create(
                user=request.user,
                user_input=topic,
                task_type="custom",
                tone="custom",
                generated_prompt=ai_reply
            )

            # RESET
            request.session["questions"] = None
            request.session["stage"] = "question"

            return redirect("home")

        # 🔥 =========================
        # QUESTION STAGE
        # 🔥 =========================

        task, _ = detect_task(user_input)
        tone, _ = detect_tone(user_input)


        # 👉 ADD RESET HERE
        request.session["chat_history"] = []
        chat_history = request.session["chat_history"]

        system_prompt = f"""
Generate ONLY 4 short questions.

User request: {user_input}

Rules:
- Each line must be a question ending with '?'
- No explanation
- No bullets
- No numbering
- No extra text
"""

        response = ollama.chat(
            model="tinyllama",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            options={"temperature": 0.3}
        )

        ai_reply = response["message"]["content"]

        ai_reply = response["message"]["content"].strip()

        # remove assistant style garbage
        bad_words = ["sure", "here", "assistant", "ai:"]
        for word in bad_words:
            ai_reply = ai_reply.replace(word, "")

        ai_reply = ai_reply.strip()

        # 🔥 STRICT QUESTION EXTRACTION
        def extract_questions(text):
            lines = text.split("\n")
            questions = []

            for l in lines:
                l = l.strip()

                if not l:
                    continue

                if not l.endswith("?"):
                    continue

                questions.append(l)

            return questions[:5]

        questions = extract_questions(ai_reply)

        # 🔥 FALLBACK (very important)
        if len(questions) < 3:
            questions = [
                "What is your goal?",
                "Who is the target audience?",
                "What tone do you prefer?",
                "Any specific requirements?"
            ]

        # Save session
        request.session["questions"] = questions
        request.session["topic"] = user_input
        request.session["stage"] = "answer"

        # Save chat
        chat_history.append({"role": "user", "content": user_input})
        chat_history.append({
            "role": "assistant",
            "content": "\n".join(["- " + q for q in questions])
        })

        request.session["chat_history"] = chat_history

        return redirect("home")

    return render(request, "home.html", {
        "profile": profile,
        "chat_history": chat_history
    })

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