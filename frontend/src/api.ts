export type User = { id: string; email: string | null; is_guest: boolean };

export type Deck = {
  id: string;
  name: string;
  created_at: string;
  card_count: number;
  due_count: number;
};

export type Card = {
  id: string;
  deck_id: string;
  question: string;
  answer: string;
  interval_days: number;
  repetitions: number;
  due_at: string;
};

export type GenerateResult = { created: Card[]; skipped_duplicates: number; truncated: boolean };

export type Stats = {
  total_cards: number;
  due_now: number;
  reviewed_today: number;
  streak_days: number;
  generations_left_today: number;
};

export type ExportFormat = "csv" | "json" | "anki";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

const TOKEN_KEY = "flashcards_token";

export const tokenStore = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

let onUnauthorized: () => void = () => {};
export function setUnauthorizedHandler(handler: () => void) {
  onUnauthorized = handler;
}

function errorMessage(status: number, body: unknown): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === "string") return detail;
  // FastAPI validation errors: [{loc, msg, ...}]
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg).replace(/^Value error, /, "");
  return status >= 500 ? "Something went wrong on our side, try again" : `Request failed (${status})`;
}

async function request(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");

  const response = await fetch(`/api${path}`, { ...init, headers });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    if (response.status === 401 && token) onUnauthorized();
    throw new ApiError(response.status, errorMessage(response.status, body));
  }
  return response;
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await request(path, init);
  return response.status === 204 ? (undefined as T) : response.json();
}

const post = (body?: unknown): RequestInit => ({
  method: "POST",
  body: body === undefined ? undefined : JSON.stringify(body),
});
const patch = (body: unknown): RequestInit => ({ method: "PATCH", body: JSON.stringify(body) });
const del: RequestInit = { method: "DELETE" };

type Token = { access_token: string };

export const api = {
  register: (email: string, password: string) => json<Token>("/auth/register", post({ email, password })),
  login: (email: string, password: string) => json<Token>("/auth/login", post({ email, password })),
  guest: () => json<Token>("/auth/guest", post()),
  claimGuest: (email: string, password: string) => json<Token>("/auth/claim", post({ email, password })),
  me: () => json<User>("/auth/me"),

  stats: () => json<Stats>("/stats"),
  decks: () => json<Deck[]>("/decks"),
  deck: (id: string) => json<Deck>(`/decks/${id}`),
  createDeck: (name: string) => json<Deck>("/decks", post({ name })),
  renameDeck: (id: string, name: string) => json<Deck>(`/decks/${id}`, patch({ name })),
  deleteDeck: (id: string) => json<void>(`/decks/${id}`, del),

  cards: (deckId: string) => json<Card[]>(`/decks/${deckId}/cards`),
  addCard: (deckId: string, question: string, answer: string) =>
    json<Card>(`/decks/${deckId}/cards`, post({ question, answer })),
  updateCard: (id: string, changes: Partial<Pick<Card, "question" | "answer">>) =>
    json<Card>(`/cards/${id}`, patch(changes)),
  deleteCard: (id: string) => json<void>(`/cards/${id}`, del),

  generateFromText: (deckId: string, text: string) =>
    json<GenerateResult>(`/decks/${deckId}/generate`, post({ text })),
  generateFromUrl: (deckId: string, url: string) =>
    json<GenerateResult>(`/decks/${deckId}/generate`, post({ url })),
  generateFromPdf: (deckId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return json<GenerateResult>(`/decks/${deckId}/generate/pdf`, { method: "POST", body: form });
  },

  due: (deckId?: string) => json<Card[]>(deckId ? `/study/due?deck_id=${deckId}` : "/study/due"),
  review: (cardId: string, grade: number) => json<Card>(`/cards/${cardId}/review`, post({ grade })),

  exportDeck: async (deckId: string, format: ExportFormat) => {
    const response = await request(`/decks/${deckId}/export?format=${format}`);
    const filename = /filename="([^"]+)"/.exec(response.headers.get("Content-Disposition") ?? "")?.[1];
    return { blob: await response.blob(), filename: filename ?? `deck.${format}` };
  },
};
