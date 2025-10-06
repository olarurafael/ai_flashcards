import React, { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [flashcards, setFlashcards] = useState([]);
  const [sessionId] = useState("demo1"); // hardcoded for MVP

  const generateFlashcards = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:8000/generate", {
        text,
        session_id: sessionId,
      });
      setFlashcards(response.data.flashcards);
    } catch (error) {
      console.error(error);
      alert("Error generating flashcards");
    }
  };

  const fetchFlashcards = async () => {
    try {
      const response = await axios.get(
        `http://127.0.0.1:8000/flashcards/${sessionId}`
      );
      setFlashcards(response.data);
    } catch (error) {
      console.error(error);
      alert("Error fetching flashcards");
    }
  };

  return (
    <div className="App">
      <h1>AI Flashcard Generator</h1>
      <textarea
        rows="6"
        cols="60"
        placeholder="Paste your text here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <br />
      <button onClick={generateFlashcards}>Generate</button>
      <button onClick={fetchFlashcards}>Fetch Saved</button>

      <div className="flashcards">
        {flashcards.map((card, index) => (
          <div key={index} className="card">
            <h3>{card.question}</h3>
            <p>{card.answer}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
