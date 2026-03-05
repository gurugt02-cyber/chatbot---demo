from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import re

app = FastAPI()

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str


# Load knowledge base ONCE (faster)
with open("knowledge.json", "r", encoding="utf-8") as f:
    KB = json.load(f)["faqs"]


# Basic stopwords
STOPWORDS = {
    "is","the","a","an","how","what","when","where","why","do","does","did",
    "we","you","i","are","to","for","of","in","on","with"
}


def clean_text(text):
    words = re.findall(r"\b\w+\b", text.lower())
    words = [w for w in words if w not in STOPWORDS]
    return set(words)


def search_kb(question):

    question_words = clean_text(question)

    best_score = 0
    best_answer = None

    for faq in KB:

        faq_words = clean_text(faq["question"])

        common = question_words.intersection(faq_words)

        if len(faq_words) == 0:
            continue

        score = len(common) / len(faq_words)

        if score > best_score:
            best_score = score
            best_answer = faq["answer"]

    # Strong threshold to prevent wrong answers
    if best_score >= 0.5:
        return best_answer

    return None


def log_question(question):
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(question + "\n")


def log_unanswered(question):

    try:
        with open("unanswered.json", "r") as f:
            data = json.load(f)
    except:
        data = []

    data.append(question)

    with open("unanswered.json", "w") as f:
        json.dump(data, f, indent=2)


@app.get("/")
def home():
    return FileResponse("chat.html")


@app.post("/chat")
def chat(request: ChatRequest):

    question = request.message

    log_question(question)

    answer = search_kb(question)

    if answer:
        return {"reply": answer}

    log_unanswered(question)

    return {
        "reply": "I don't have the answer to this right now, but I have recorded this question so the team can add it to the knowledge base."
    }
