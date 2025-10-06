import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [flashcards, setFlashcards] = useState([]);
  const [sessionId, setSessionId] = useState("");

  // Unique session ID 
  useEffect(() => {
    let existingId = localStorage.getItem("session_id");
    if (!existingId) {
      existingId = "user-" + Math.random().toString(36).substring(2, 8);
      localStorage.setItem("session_id", existingId);
    }
    setSessionId(existingId);
  }, []);

  const generateFlashcards = async () => {
    try {
      const response = await axios.post("https://ai-flashcards-1-rss9.onrender.com/generate", {
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
        `https://ai-flashcards-1-rss9.onrender.com/flashcards/${sessionId}`
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
        placeholder="Paste your text here... First command might take a while."
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

      <p style={{ marginTop: "40px", fontSize: "0.8rem", color: "#555" }}>
        Session ID: <b>{sessionId}</b>
      </p>
    </div>
  );
}

export default App;
