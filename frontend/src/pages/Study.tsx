import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { api, type Card } from "../api";

// SM-2 grades sent for each button (see backend/app/srs.py).
export const GRADES = [
  { grade: 1, label: "Again", key: "1" },
  { grade: 3, label: "Hard", key: "2" },
  { grade: 4, label: "Good", key: "3" },
  { grade: 5, label: "Easy", key: "4" },
] as const;

export default function Study() {
  const [params] = useSearchParams();
  const deckId = params.get("deck") ?? undefined;
  const [queue, setQueue] = useState<Card[] | null>(null);
  const [revealed, setRevealed] = useState(false);
  const [done, setDone] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.due(deckId).then(setQueue).catch((err) => setError(err.message));
  }, [deckId]);

  const card = queue?.[0];

  const grade = useCallback(
    async (value: number) => {
      if (!card) return;
      try {
        await api.review(card.id, value);
        // A lapsed card comes back at the end of this session, as in Anki.
        setQueue((q) => (value < 3 ? [...q!.slice(1), card] : q!.slice(1)));
        setRevealed(false);
        setDone((n) => n + 1);
      } catch (err) {
        setError((err as Error).message);
      }
    },
    [card],
  );

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) return;
      if (!revealed && (event.key === " " || event.key === "Enter")) {
        event.preventDefault();
        setRevealed(true);
      } else if (revealed) {
        const match = GRADES.find((g) => g.key === event.key);
        if (match) grade(match.grade);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [revealed, grade]);

  const back = deckId ? `/decks/${deckId}` : "/";

  if (error) return <p className="error">{error}</p>;
  if (!queue) return <p className="muted">Loading…</p>;

  if (!card) {
    return (
      <div className="study-done">
        <h2>{done > 0 ? "Session complete" : "Nothing due right now"}</h2>
        <p className="muted">
          {done > 0
            ? `You reviewed ${done} ${done === 1 ? "card" : "cards"}. They'll come back when you're about to forget them.`
            : "Come back later, or generate new cards."}
        </p>
        <Link to={back} className="button primary">
          Back
        </Link>
      </div>
    );
  }

  return (
    <div className="study">
      <div className="row muted small study-progress">
        <Link to={back} className="back">
          ← Stop
        </Link>
        <span>{queue.length} left</span>
      </div>

      <div className={revealed ? "flashcard revealed" : "flashcard"}>
        <p className="q">{card.question}</p>
        {revealed && <p className="a">{card.answer}</p>}
      </div>

      {revealed ? (
        <div className="grades">
          {GRADES.map(({ grade: value, label, key }) => (
            <button key={value} className={`grade grade-${label.toLowerCase()}`} onClick={() => grade(value)}>
              {label}
              <kbd>{key}</kbd>
            </button>
          ))}
        </div>
      ) : (
        <button className="primary large reveal" onClick={() => setRevealed(true)}>
          Show answer <kbd>Space</kbd>
        </button>
      )}
    </div>
  );
}
