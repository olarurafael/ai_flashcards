import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, type Card, type Deck, type ExportFormat } from "../api";
import Generate from "./Generate";

export default function DeckPage() {
  const { deckId = "" } = useParams();
  const navigate = useNavigate();
  const [deck, setDeck] = useState<Deck | null>(null);
  const [cards, setCards] = useState<Card[]>([]);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    Promise.all([api.deck(deckId), api.cards(deckId)])
      .then(([deck, cards]) => {
        setDeck(deck);
        setCards(cards);
      })
      .catch((err) => setError(err.message));
  }, [deckId]);

  useEffect(reload, [reload]);

  async function rename() {
    const name = window.prompt("Rename deck", deck?.name)?.trim();
    if (name) setDeck(await api.renameDeck(deckId, name));
  }

  async function remove() {
    if (!window.confirm(`Delete "${deck?.name}" and all ${cards.length} cards?`)) return;
    await api.deleteDeck(deckId);
    navigate("/");
  }

  async function download(format: ExportFormat) {
    const { blob, filename } = await api.exportDeck(deckId, format);
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
  }

  if (error) return <p className="error">{error}</p>;
  if (!deck) return <p className="muted">Loading…</p>;

  return (
    <>
      <Link to="/" className="back">
        ← All decks
      </Link>
      <div className="section-head">
        <div>
          <h2>{deck.name}</h2>
          <p className="muted small">
            {deck.card_count} cards · {deck.due_count} due now
          </p>
        </div>
        <div className="row">
          {deck.due_count > 0 && (
            <Link to={`/study?deck=${deckId}`} className="button primary">
              Study {deck.due_count} due
            </Link>
          )}
          <button className="ghost" onClick={rename}>
            Rename
          </button>
          <button className="ghost danger" onClick={remove}>
            Delete
          </button>
        </div>
      </div>

      <Generate deckId={deckId} onGenerated={reload} />

      <div className="section-head">
        <h3>Cards</h3>
        {cards.length > 0 && (
          <div className="row small">
            <span className="muted">Export:</span>
            <button className="link" onClick={() => download("anki")}>
              Anki
            </button>
            <button className="link" onClick={() => download("csv")}>
              CSV
            </button>
            <button className="link" onClick={() => download("json")}>
              JSON
            </button>
          </div>
        )}
      </div>

      <AddCard deckId={deckId} onAdded={reload} />
      {cards.length === 0 && <p className="empty">No cards yet. Generate some above or add one by hand.</p>}
      <ul className="card-list">
        {cards.map((card) => (
          <CardRow key={card.id} card={card} onChanged={reload} />
        ))}
      </ul>
    </>
  );
}

function AddCard({ deckId, onAdded }: { deckId: string; onAdded: () => void }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      await api.addCard(deckId, question, answer);
      setQuestion("");
      setAnswer("");
      setError(null);
      onAdded();
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <form className="inline-form" onSubmit={submit}>
      <input placeholder="Question" aria-label="Question" required maxLength={500} value={question} onChange={(e) => setQuestion(e.target.value)} />
      <input placeholder="Answer" aria-label="Answer" required maxLength={2000} value={answer} onChange={(e) => setAnswer(e.target.value)} />
      <button>Add card</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}

function nextReview(card: Card): string {
  if (card.repetitions === 0) return "new";
  const days = Math.round((new Date(card.due_at).getTime() - Date.now()) / 86_400_000);
  if (days <= 0) return "due";
  return days === 1 ? "in 1 day" : `in ${days} days`;
}

function CardRow({ card, onChanged }: { card: Card; onChanged: () => void }) {
  const [editing, setEditing] = useState(false);
  const [question, setQuestion] = useState(card.question);
  const [answer, setAnswer] = useState(card.answer);

  async function save(event: FormEvent) {
    event.preventDefault();
    await api.updateCard(card.id, { question, answer });
    setEditing(false);
    onChanged();
  }

  async function remove() {
    await api.deleteCard(card.id);
    onChanged();
  }

  if (editing) {
    return (
      <li className="card-row">
        <form className="card-edit" onSubmit={save}>
          <input aria-label="Question" required maxLength={500} value={question} onChange={(e) => setQuestion(e.target.value)} />
          <textarea aria-label="Answer" required maxLength={2000} rows={2} value={answer} onChange={(e) => setAnswer(e.target.value)} />
          <div className="row">
            <button className="primary small">Save</button>
            <button type="button" className="ghost small" onClick={() => setEditing(false)}>
              Cancel
            </button>
          </div>
        </form>
      </li>
    );
  }

  return (
    <li className="card-row">
      <div>
        <p className="q">{card.question}</p>
        <p className="a">{card.answer}</p>
      </div>
      <div className="card-meta">
        <span className="pill subtle">{nextReview(card)}</span>
        <button className="link small" onClick={() => setEditing(true)}>
          Edit
        </button>
        <button className="link small danger" onClick={remove}>
          Delete
        </button>
      </div>
    </li>
  );
}
