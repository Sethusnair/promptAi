from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
from training_data import task_data, tone_data

# -----------------------------
# DATA AUGMENTATION (ADD HERE)
# -----------------------------
augmented_task_data = []

for text, label in task_data:
    augmented_task_data.append((text, label))
    augmented_task_data.append((text + " please", label))
    augmented_task_data.append(("can you " + text, label))
    augmented_task_data.append(("help me " + text, label))

task_data = augmented_task_data


# Clean function
def clean_text(text):
    return text.lower()


# ---------- TASK MODEL ----------
task_texts = [clean_text(x[0]) for x in task_data]
task_labels = [x[1] for x in task_data]

task_vectorizer = TfidfVectorizer(
    ngram_range=(1,2),
    stop_words='english',
    max_features=800
)

X_task = task_vectorizer.fit_transform(task_texts)

task_model = LogisticRegression(max_iter=1000)
task_model.fit(X_task, task_labels)

joblib.dump(task_model, "task_model.pkl")
joblib.dump(task_vectorizer, "task_vectorizer.pkl")


# ---------- TONE MODEL ----------
tone_texts = [clean_text(x[0]) for x in tone_data]
tone_labels = [x[1] for x in tone_data]

tone_vectorizer = TfidfVectorizer(
    ngram_range=(1,2),
    stop_words='english',
    max_features=500
)

X_tone = tone_vectorizer.fit_transform(tone_texts)

tone_model = LogisticRegression(max_iter=1000)
tone_model.fit(X_tone, tone_labels)

joblib.dump(tone_model, "tone_model.pkl")
joblib.dump(tone_vectorizer, "tone_vectorizer.pkl")

print("Improved models trained!")