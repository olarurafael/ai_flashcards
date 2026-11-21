from types import SimpleNamespace

import httpx
import openai
import pytest

from app.llm import GeneratedCard, GeneratedDeck, GenerationError, OpenAIGenerator


def generator_returning(result=None, error: Exception | None = None):
    """An OpenAIGenerator whose API call is replaced by a stub."""
    generator = OpenAIGenerator(api_key="test-key", model="gpt-4o-mini")
    calls = []

    def parse(**kwargs):
        calls.append(kwargs)
        if error:
            raise error
        return result

    generator._client = SimpleNamespace(responses=SimpleNamespace(parse=parse))
    return generator, calls


def response(status="completed", cards=None):
    parsed = GeneratedDeck(cards=cards) if cards is not None else None
    return SimpleNamespace(status=status, output_parsed=parsed)


def test_returns_parsed_cards_capped_at_max():
    cards = [GeneratedCard(question=f"Q{i}", answer=f"A{i}") for i in range(5)]
    generator, calls = generator_returning(response(cards=cards))

    assert [c.question for c in generator.generate("some text", max_cards=3)] == ["Q0", "Q1", "Q2"]

    request = calls[0]
    assert request["text_format"] is GeneratedDeck
    assert request["input"] == "<document>\nsome text\n</document>"
    assert "at most 3 cards" in request["instructions"]


def test_incomplete_response_is_an_error():
    generator, _ = generator_returning(response(status="incomplete", cards=[]))
    with pytest.raises(GenerationError, match="no flashcards"):
        generator.generate("text", max_cards=5)


def test_refusal_is_an_error():
    generator, _ = generator_returning(response(cards=None))
    with pytest.raises(GenerationError, match="Couldn't"):
        generator.generate("text", max_cards=5)


def _status_error(cls, status):
    request = httpx.Request("POST", "https://api.openai.com/v1/responses")
    return cls("error", response=httpx.Response(status, request=request), body=None)


@pytest.mark.parametrize(
    "error, message",
    [
        (_status_error(openai.RateLimitError, 429), "busy"),
        (_status_error(openai.InternalServerError, 500), "unavailable"),
        (_status_error(openai.AuthenticationError, 401), "unavailable"),
        (openai.APITimeoutError(httpx.Request("POST", "https://api.openai.com")), "too long"),
    ],
)
def test_api_errors_become_generation_errors(error, message):
    generator, _ = generator_returning(error=error)
    with pytest.raises(GenerationError, match=message):
        generator.generate("text", max_cards=5)
