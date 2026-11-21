import { useState, type FormEvent } from "react";
import { api } from "../api";
import { useAuth } from "../auth";

export default function Welcome() {
  const { signIn } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function run(action: () => Promise<{ access_token: string }>) {
    setBusy(true);
    setError(null);
    try {
      await signIn((await action()).access_token);
    } catch (err) {
      setError((err as Error).message);
      setBusy(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    run(() => (mode === "login" ? api.login(email, password) : api.register(email, password)));
  }

  return (
    <div className="welcome">
      <section className="pitch">
        <h1>Turn anything you read into flashcards you'll remember.</h1>
        <p className="lead">
          Paste notes, upload a PDF or drop in a link. AI writes the cards, and spaced repetition schedules each one
          right before you'd forget it.
        </p>
        <ul className="features">
          <li>
            <strong>Text, PDF or URL</strong> in, focused question–answer cards out
          </li>
          <li>
            <strong>SM-2 scheduling</strong>, the algorithm behind Anki, with a daily review queue
          </li>
          <li>
            <strong>Export</strong> to CSV, JSON or straight into Anki
          </li>
        </ul>
        <button className="primary large" disabled={busy} onClick={() => run(api.guest)}>
          Try it now, no sign-up
        </button>
      </section>

      <form className="panel auth" onSubmit={submit}>
        <div className="tabs" role="tablist">
          <button
            type="button"
            role="tab"
            aria-selected={mode === "login"}
            className={mode === "login" ? "tab active" : "tab"}
            onClick={() => setMode("login")}
          >
            Sign in
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === "register"}
            className={mode === "register" ? "tab active" : "tab"}
            onClick={() => setMode("register")}
          >
            Create account
          </button>
        </div>
        <label>
          Email
          <input type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>
          Password
          <input
            type="password"
            required
            minLength={8}
            maxLength={64}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="primary" disabled={busy}>
          {mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>
    </div>
  );
}
