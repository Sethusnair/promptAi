import joblib
import ollama

# load models
task_model = joblib.load("core/task_model.pkl")
task_vectorizer = joblib.load("core/task_vectorizer.pkl")

tone_model = joblib.load("core/tone_model.pkl")
tone_vectorizer = joblib.load("core/tone_vectorizer.pkl")


def detect_task(text):
    vec = task_vectorizer.transform([text])
    probs = task_model.predict_proba(vec)[0]
    idx = probs.argmax()
    task = str(task_model.classes_[idx])
    confidence = probs[idx]
    return task, confidence


def detect_tone(text):
    vec = tone_vectorizer.transform([text])
    probs = tone_model.predict_proba(vec)[0]
    idx = probs.argmax()
    tone = str(tone_model.classes_[idx])
    confidence = probs[idx]
    return tone, confidence


def generate_prompt(user_input, task, tone, context=None):

    if context is None:
        system_prompt = f"""
You are an expert prompt engineer AI.

Task Type: {task}
Tone: {tone}

Your job is to help users build a high quality AI prompt.

Step 1:
If the user gives only a short request, ask structured questions to gather details.

Use a friendly tone and bullet points.

Example format:

AI: [smiling] Hey there! Let's refine this idea.

Ask questions like:
- Goal
- Audience
- Budget
- Constraints
- Style preferences
- Output format

Do NOT generate the final prompt yet.
Only ask questions.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]

    else:
        system_prompt = f"""
You are an expert prompt engineer.

Task Type: {task}
Tone: {tone}

The user has answered clarification questions.

Now generate a **clear, detailed, structured AI prompt** based on the conversation.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context}
        ]

    response = ollama.chat(
        model="tinyllama",
        messages=messages
    )

    return response['message']['content']