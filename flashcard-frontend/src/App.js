import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [text, setText] = useState("");
  const [flashcards, setFlashcards] = useState([]);
  const [sessionId, setSessionId] = useState("");
  const [studyMode, setStudyMode] = useState(false);
  const [revealed, setRevealed] = useState([]); // track which answers are shown

  // ✅ Create or restore unique session ID
  useEffect(() => {
    let existingId = localStorage.getItem("session_id");
    if (!existingId) {
      existingId = "user-" + Math.random().toString(36).substring(2, 8);
      localStorage.setItem("session_id", existingId);
    }
    setSessionId(existingId);
  }, []);

  // ✅ Generate flashcards via backend
  const generateFlashcards = async () => {
    try {
      const response = await axios.post("https://ai-flashcards-1-rss9.onrender.com/generate", {
        text,
        session_id: sessionId,
      });
      setFlashcards(response.data.flashcards);
      setRevealed(Array(response.data.flashcards.length).fill(false));
    } catch (error) {
      console.error(error);
      alert("Error generating flashcards");
    }
  };

  // ✅ Fetch flashcards from DB
  const fetchFlashcards = async () => {
    try {
      const response = await axios.get(
        `https://ai-flashcards-1-rss9.onrender.com/flashcards/${sessionId}`
      );
      setFlashcards(response.data);
      setRevealed(Array(response.data.length).fill(false));
    } catch (error) {
      console.error(error);
      alert("Error fetching flashcards");
    }
  };

  // ✅ Download as JSON or CSV
  const downloadFlashcards = (format = "json") => {
    if (flashcards.length === 0) {
      alert("No flashcards to download!");
      return;
    }

    if (format === "json") {
      const blob = new Blob([JSON.stringify(flashcards, null, 2)], { type: "application/json" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `flashcards_${sessionId}.json`;
      link.click();
    } else if (format === "csv") {
      const csvContent =
        "Question,Answer\n" +
        flashcards
          .map(f => `"${f.question.replace(/"/g, '""')}","${f.answer.replace(/"/g, '""')}"`)
          .join("\n");
      const blob = new Blob([csvContent], { type: "text/csv" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `flashcards_${sessionId}.csv`;
      link.click();
    }
  };

  // ✅ Study Mode toggle
  const toggleStudyMode = () => {
    setStudyMode(!studyMode);
    setRevealed(Array(flashcards.length).fill(false)); // reset revealed answers
  };

  // ✅ Reveal or hide answer per card
  const toggleReveal = (index) => {
    const updated = [...revealed];
    updated[index] = !updated[index];
    setRevealed(updated);
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
      
      <div className="button-group">
        <button onClick={generateFlashcards}>Generate</button>
        <button onClick={fetchFlashcards}>Fetch Saved</button>
        <div className="download-buttons">
          <button onClick={() => downloadFlashcards("json")}>Download JSON</button>
          <button onClick={() => downloadFlashcards("csv")}>Download CSV</button>
        </div>
        <button className="study-btn" onClick={toggleStudyMode}>
          {studyMode ? "Exit Study Mode" : "Enter Study Mode"}
        </button>
      </div>
      <div className="flashcards">
        {flashcards.map((card, index) => (
          <div key={index} className="card">
            <h3>{card.question}</h3>
            {studyMode ? (
              <>
                {!revealed[index] ? (
                  <button onClick={() => toggleReveal(index)}>Show Answer</button>
                ) : (
                  <p><b>{card.answer}</b></p>
                )}
              </>
            ) : (
              <p>{card.answer}</p>
            )}
          </div>
        ))}
      </div>

      <p className="session-info">
        Session ID: <b>{sessionId}</b>
      </p>
    </div>
  );
}

export default App;
