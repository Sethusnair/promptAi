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


def generate_prompt(user_input, task, tone):

    system_prompt = f"""
You are an expert prompt engineer.

Task Type: {task}
Tone: {tone}

Rewrite the user's request into a clear, detailed, and professional AI prompt.
Improve grammar and structure while keeping the intent.
"""

    response = ollama.chat(
        model="tinyllama",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )

    return response['message']['content']