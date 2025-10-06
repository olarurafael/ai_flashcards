from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware
import os
from openai import OpenAI
import re
import json
from dotenv import load_dotenv
import os


load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ai-flashcard-app-olarur.netlify.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB Model
class Flashcard(Base):
    __tablename__ = "flashcards"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

Base.metadata.create_all(bind=engine)

# Request schema
class TextInput(BaseModel):
    text: str
    session_id: str

@app.post("/generate")
def generate_flashcards(input: TextInput):
    prompt = f"""
    Generate flashcards in JSON format from the following text.
    Use concise question-answer pairs.
    Text: {input.text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or gpt-3.5-turbo if you want cheaper
        messages=[
            {"role": "system", "content": "You are a flashcard generator."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    raw_content = response.choices[0].message.content

    # Strip Markdown code block fences if present
    clean_content = re.sub(r"^```(json)?|```$", "", raw_content.strip(), flags=re.MULTILINE)

    try:
        flashcards_json = json.loads(clean_content)
    except json.JSONDecodeError:
        flashcards_json = [{"question": "Parse error", "answer": raw_content}]

    # Save to DB
    db = SessionLocal()
    flashcards = []
    for card in flashcards_json:
        question = card.get("question", "")
        answer = card.get("answer", "")
        fc = Flashcard(session_id=input.session_id, question=question, answer=answer)
        db.add(fc)
        flashcards.append({"question": question, "answer": answer})
    db.commit()
    db.close()

    return {"flashcards": flashcards}


@app.get("/flashcards/{session_id}")
def get_flashcards(session_id: str):
    db = SessionLocal()
    cards = db.query(Flashcard).filter(Flashcard.session_id == session_id).all()
    db.close()
    return [{"question": c.question, "answer": c.answer} for c in cards]
