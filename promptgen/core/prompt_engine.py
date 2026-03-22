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

