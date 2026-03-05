from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json

app = FastAPI()

# Enable CORS (important for hosting)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str


# Load knowledge base ONCE at startup
with open("knowledge.json", "r", encoding="utf-8") as f:
    kb = json.load(f)


# Simple stopword list
stop_words = {
    "what","is","how","the","a","an","to","of","for",
    "do","we","are","can","you","please","tell"
}


# Serve chatbot UI
@app.get("/")
def home():
    return FileResponse("chat.html")


def log_question(question):
    with open("logs.txt", "a", encoding="utf-8") as f:
        f.write(question + "\n")


def log_unanswered(question):
    try:
        with open("unanswered.json", "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        data = []

    if question not in data:
        data.append(question)

    with open("unanswered.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def clean_text(text):

    words = text.lower().split()

    words = [w for w in words if w not in stop_words]

    return set(words)


def search_kb(question):

    question_words = clean_text(question)

    best_score = 0
    best_answer = None

    for faq in kb["faqs"]:

        faq_words = clean_text(faq["question"])

        score = len(question_words.intersection(faq_words))

        if score > best_score:
            best_score = score
            best_answer = faq["answer"]

    if best_score >= 2:
        return best_answer

    return None


@app.post("/chat")
def chat(request: ChatRequest):

    question = request.message.strip()

    log_question(question)

    answer = search_kb(question)

    if answer:
        return {"reply": answer}

    log_unanswered(question)

    return {
        "reply": "I don't have the answer to this right now, but I have recorded this question so the team can add it to the knowledge base."
    }