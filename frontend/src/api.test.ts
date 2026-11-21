import { api, ApiError, setUnauthorizedHandler, tokenStore } from "./api";

function mockFetch(status: number, body: unknown) {
  return vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } }),
  );
}

afterEach(() => {
  vi.restoreAllMocks();
  tokenStore.clear();
});

test("sends the bearer token and JSON body", async () => {
  tokenStore.set("abc");
  const fetchMock = mockFetch(201, { id: "d1", name: "Bio", created_at: "", card_count: 0, due_count: 0 });

  await api.createDeck("Bio");

  const [url, init] = fetchMock.mock.calls[0];
  expect(url).toBe("/api/decks");
  const headers = new Headers(init!.headers);
  expect(headers.get("Authorization")).toBe("Bearer abc");
  expect(headers.get("Content-Type")).toBe("application/json");
  expect(init!.body).toBe(JSON.stringify({ name: "Bio" }));
});

test("surfaces the API's error message", async () => {
  mockFetch(429, { detail: "You have used today's generations, try again tomorrow" });
  await expect(api.generateFromText("d1", "text")).rejects.toEqual(
    new ApiError(429, "You have used today's generations, try again tomorrow"),
  );
});

test("turns validation errors into a readable message", async () => {
  mockFetch(422, { detail: [{ loc: ["body"], msg: "Value error, Provide either text or url" }] });
  await expect(api.generateFromText("d1", "")).rejects.toThrow("Provide either text or url");
});

test("signs out when the token is rejected", async () => {
  tokenStore.set("expired");
  const handler = vi.fn();
  setUnauthorizedHandler(handler);
  mockFetch(401, { detail: "Not authenticated" });

  await expect(api.decks()).rejects.toBeInstanceOf(ApiError);
  expect(handler).toHaveBeenCalled();
});
