# AI Flashcard Generator

An AI-powered flashcard web app that converts any text into concise question–answer pairs using OpenAI’s GPT-4 model.  
Built with **FastAPI**, **React**, and **PostgreSQL**, it provides an intuitive interface for generating, saving, and studying flashcards.

---

## Live Demo
**Frontend:** [https://ai-flashcard-app-olarur.netlify.app](https://ai-flashcard-app-olarur.netlify.app)  
**Backend API:** [https://ai-flashcards-1-rss9.onrender.com](https://ai-flashcards-1-rss9.onrender.com)

---

## Tech Stack

**Frontend**
- React (Create React App)
- Axios for API calls
- Responsive CSS styling
- `localStorage` for session persistence

**Backend**
- FastAPI with SQLAlchemy ORM
- PostgreSQL database
- OpenAI GPT-4 API integration
- CORS middleware and environment variable configuration
- Deployed on Render

**Deployment**
- Frontend hosted on Netlify  
- Backend hosted on Render  
- Continuous deployment via GitHub

---

## Features
- Generate flashcards automatically from any text  
- Unique session IDs persisted in the browser  
- Duplicate prevention for cleaner datasets  
- Download flashcards as **CSV** or **JSON**  
- Interactive **Study Mode** for self-testing  
- Secure full-stack integration with CORS

---

## API Endpoints

| Method | Endpoint | Description |
|:------:|:----------|:-------------|
| `POST` | `/generate` | Generate flashcards from text input |
| `GET`  | `/flashcards/{session_id}` | Retrieve flashcards for a specific session |

Example payload:
```json
{
  "text": "Photosynthesis is the process by which plants convert sunlight into energy.",
  "session_id": "user-3f8a7c"
}
```

---

## Local Setup

### Backend
```bash
cd app
pip install -r requirements.txt
uvicorn main:app --reload
```

Create a `.env` file:
```
OPENAI_API_KEY=your_openai_key
DATABASE_URL=your_postgres_url
```

### Frontend
```bash
cd flashcard-frontend
npm install
npm start
```

---

## How It Works
1. Enter text into the input box.  
2. Click **Generate** to create AI-generated flashcards.  
3. Click **Fetch Saved** to view previously generated cards.  
4. Use **Study Mode** to review them interactively.  
5. Download your flashcards in CSV or JSON format.

---

## Author
**Rafael Olaru**  
[LinkedIn](https://www.linkedin.com/in/rafaelolaru/)  
[Live Demo](https://ai-flashcard-app-olarur.netlify.app)

---

> Built to make studying faster, smarter, and more interactive.
