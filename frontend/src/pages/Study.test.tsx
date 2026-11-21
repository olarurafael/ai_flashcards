import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { api, type Card } from "../api";
import Study from "./Study";

function card(id: string, question: string): Card {
  return { id, deck_id: "d1", question, answer: `${question} answer`, interval_days: 0, repetitions: 0, due_at: "" };
}

function renderStudy() {
  return render(
    <MemoryRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <Study />
    </MemoryRouter>,
  );
}

afterEach(() => vi.restoreAllMocks());

test("reveals the answer and sends the chosen grade", async () => {
  vi.spyOn(api, "due").mockResolvedValue([card("c1", "First"), card("c2", "Second")]);
  const review = vi.spyOn(api, "review").mockResolvedValue(card("c1", "First"));
  renderStudy();

  expect(await screen.findByText("First")).toBeInTheDocument();
  expect(screen.queryByText("First answer")).not.toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: /show answer/i }));
  expect(screen.getByText("First answer")).toBeInTheDocument();

  await userEvent.click(screen.getByRole("button", { name: /good/i }));
  expect(review).toHaveBeenCalledWith("c1", 4);
  expect(await screen.findByText("Second")).toBeInTheDocument();
});

test("keyboard: space reveals, number keys grade", async () => {
  vi.spyOn(api, "due").mockResolvedValue([card("c1", "Only")]);
  const review = vi.spyOn(api, "review").mockResolvedValue(card("c1", "Only"));
  renderStudy();

  await screen.findByText("Only");
  await userEvent.keyboard(" ");
  await userEvent.keyboard("4");
  expect(review).toHaveBeenCalledWith("c1", 5);
  expect(await screen.findByText("Session complete")).toBeInTheDocument();
});

test("a lapsed card comes back at the end of the session", async () => {
  vi.spyOn(api, "due").mockResolvedValue([card("c1", "Tricky"), card("c2", "Easy one")]);
  vi.spyOn(api, "review").mockResolvedValue(card("c1", "Tricky"));
  renderStudy();

  await screen.findByText("Tricky");
  await userEvent.keyboard(" 1");
  expect(await screen.findByText("Easy one")).toBeInTheDocument();
  await userEvent.keyboard(" 3");
  expect(await screen.findByText("Tricky")).toBeInTheDocument();
});

test("shows an empty state when nothing is due", async () => {
  vi.spyOn(api, "due").mockResolvedValue([]);
  renderStudy();
  expect(await screen.findByText("Nothing due right now")).toBeInTheDocument();
});
