import { useState, type FormEvent } from "react";
import { Link, Navigate, Route, Routes } from "react-router-dom";
import { api } from "./api";
import { useAuth } from "./auth";
import DeckPage from "./pages/DeckPage";
import Decks from "./pages/Decks";
import Study from "./pages/Study";
import Welcome from "./pages/Welcome";

export default function App() {
  const { user, loading, signOut } = useAuth();

  if (loading) return <div className="center muted">Loading…</div>;
  if (!user) return <Welcome />;

  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">
          <img src="/favicon.svg" alt="" width={22} height={22} />
          AI Flashcards
        </Link>
        <div className="topbar-right">
          <span className="muted small">{user.is_guest ? "Guest" : user.email}</span>
          <button className="ghost small" onClick={signOut}>
            Sign out
          </button>
        </div>
      </header>
      {user.is_guest && <GuestBanner />}
      <main className="container">
        <Routes>
          <Route path="/" element={<Decks />} />
          <Route path="/decks/:deckId" element={<DeckPage />} />
          <Route path="/study" element={<Study />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}

function GuestBanner() {
  const { signIn } = useAuth();
  const [open, setOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function claim(event: FormEvent) {
    event.preventDefault();
    try {
      await signIn((await api.claimGuest(email, password)).access_token);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <div className="banner">
      {open ? (
        <form className="inline-form" onSubmit={claim}>
          <input type="email" required placeholder="Email" aria-label="Email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <input
            type="password"
            required
            minLength={8}
            maxLength={64}
            placeholder="Password (8+ characters)"
            aria-label="Password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="primary small">Save my decks</button>
          {error && <span className="error">{error}</span>}
        </form>
      ) : (
        <p>
          You're using a guest account, so your decks are lost when you sign out.{" "}
          <button className="link" onClick={() => setOpen(true)}>
            Create an account to keep them
          </button>
        </p>
      )}
    </div>
  );
}
