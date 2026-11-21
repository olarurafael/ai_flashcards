import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, type Deck, type Stats } from "../api";

export default function Decks() {
  const navigate = useNavigate();
  const [decks, setDecks] = useState<Deck[] | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.decks(), api.stats()])
      .then(([decks, stats]) => {
        setDecks(decks);
        setStats(stats);
      })
      .catch((err) => setError(err.message));
  }, []);

  async function createDeck(event: FormEvent) {
    event.preventDefault();
    try {
      const deck = await api.createDeck(name);
      navigate(`/decks/${deck.id}`);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <>
      {stats && (
        <section className="stats">
          <Stat label="Due now" value={stats.due_now} />
          <Stat label="Reviewed today" value={stats.reviewed_today} />
          <Stat label="Day streak" value={stats.streak_days} />
          <Stat label="Total cards" value={stats.total_cards} />
          {stats.due_now > 0 && (
            <Link to="/study" className="button primary stats-cta">
              Study all due cards
            </Link>
          )}
        </section>
      )}

      <div className="section-head">
        <h2>Your decks</h2>
      </div>
      {error && <p className="error">{error}</p>}

      <form className="inline-form" onSubmit={createDeck}>
        <input
          placeholder="New deck, e.g. Organic chemistry"
          aria-label="New deck name"
          required
          maxLength={200}
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button className="primary">Create deck</button>
      </form>

      {decks === null && !error && <p className="muted">Loading…</p>}
      {decks?.length === 0 && (
        <p className="empty">No decks yet. Create one, then generate cards from your notes, a PDF or a link.</p>
      )}
      <ul className="deck-grid">
        {decks?.map((deck) => (
          <li key={deck.id}>
            <Link to={`/decks/${deck.id}`} className="deck-tile">
              <span className="deck-name">{deck.name}</span>
              <span className="muted small">
                {deck.card_count} {deck.card_count === 1 ? "card" : "cards"}
              </span>
              {deck.due_count > 0 && <span className="pill">{deck.due_count} due</span>}
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="stat">
      <span className="stat-value">{value}</span>
      <span className="muted small">{label}</span>
    </div>
  );
}
