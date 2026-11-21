import { useState, type FormEvent } from "react";
import { api, type GenerateResult } from "../api";

type Source = "text" | "url" | "pdf";

const SOURCES: { id: Source; label: string }[] = [
  { id: "text", label: "Paste text" },
  { id: "url", label: "From a link" },
  { id: "pdf", label: "Upload PDF" },
];

export default function Generate({ deckId, onGenerated }: { deckId: string; onGenerated: () => void }) {
  const [source, setSource] = useState<Source>("text");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<GenerateResult | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const generated =
        source === "text"
          ? await api.generateFromText(deckId, text)
          : source === "url"
            ? await api.generateFromUrl(deckId, url)
            : await api.generateFromPdf(deckId, file!);
      setResult(generated);
      setText("");
      setUrl("");
      onGenerated();
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="panel generate" onSubmit={submit}>
      <div className="tabs" role="tablist">
        {SOURCES.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={source === id}
            className={source === id ? "tab active" : "tab"}
            onClick={() => setSource(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {source === "text" && (
        <textarea
          rows={7}
          required
          aria-label="Text to turn into flashcards"
          placeholder="Paste lecture notes, an article, a chapter…"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      )}
      {source === "url" && (
        <input
          type="url"
          required
          aria-label="Page URL"
          placeholder="https://en.wikipedia.org/wiki/Spaced_repetition"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
        />
      )}
      {source === "pdf" && (
        <input
          type="file"
          required
          accept="application/pdf"
          aria-label="PDF file"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
      )}

      <div className="row">
        <button className="primary" disabled={busy}>
          {busy ? "Writing cards…" : "Generate flashcards"}
        </button>
        <span className="muted small">Up to 20 cards per run. Long inputs are trimmed to the first ~20,000 characters.</span>
      </div>

      {error && <p className="error">{error}</p>}
      {result && (
        <p className="success">
          Added {result.created.length} {result.created.length === 1 ? "card" : "cards"}
          {result.skipped_duplicates > 0 && `, skipped ${result.skipped_duplicates} already in this deck`}
          {result.truncated && ". The input was long, so only the first part was used"}.
        </p>
      )}
    </form>
  );
}
