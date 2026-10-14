"""`.venv/bin/python test_app.py` — no network, no embedding model. Pins the behaviour the chatbot's safety depends on."""
import os
import sys
import types

os.environ.setdefault("CHAT_MODEL", "test/model")
os.environ.setdefault("OPENROUTER_API_KEY", "test")
fake = types.ModuleType("sentence_transformers")  # app.py loads bge-m3 at import; these tests never embed
fake.SentenceTransformer, fake.util = (lambda *a, **k: None), None
sys.modules["sentence_transformers"] = fake
import app


class Resp:
    def __init__(self, content=None, status=200):
        self.content, self.status = content, status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(self.status)

    def json(self):
        return {"choices": [{"message": {"content": self.content}}]}


def with_responses(responses):
    """Make app.llm see these responses in order; return how many calls were made."""
    calls = []
    app.requests.post = lambda *a, **k: (calls.append(1), responses[len(calls) - 1])[1]
    app.time.sleep = lambda s: None
    return calls


def test_llm_retries_once_on_empty_then_succeeds():
    calls = with_responses([Resp(None), Resp("ok")])  # free models sometimes return empty content
    assert app.llm([]) == "ok" and len(calls) == 2


def test_llm_gives_up_after_one_retry():
    calls = with_responses([Resp(status=429), Resp(status=429), Resp("never")])
    try:
        app.llm([])
    except RuntimeError:
        assert len(calls) == 2
    else:
        raise AssertionError("should raise after the retry")


def test_classify_fails_closed_to_escalate():
    # An outage must hand the customer to a human, never let an unfiltered message through to the answer step.
    with_responses([Resp(status=500), Resp(status=500)])
    category, reason = app.classify("How much is the Stark 3?")
    assert category == "ESCALATE"
    assert "classifier failed" in reason  # support staff must be able to tell a bot outage from an angry customer


def test_classify_unknown_category_escalates():
    with_responses([Resp('{"category": "MAKE_UP_SOMETHING"}')])
    category, reason = app.classify("hi")
    assert category == "ESCALATE" and "MAKE_UP_SOMETHING" in reason


def test_ticket_records_reason():
    import json
    import tempfile
    from pathlib import Path

    app.TICKETS = Path(tempfile.mkdtemp()) / "tickets.jsonl"
    with_responses([Resp('{"category": "ESCALATE", "reason": "damaged on arrival"}')])
    reply, route, _ = app.answer("My ship arrived damaged", [])
    record = json.loads(app.TICKETS.read_text())
    assert route == "ESCALATE" and record["reason"] == "damaged on arrival"
    assert "damaged on arrival" not in reply  # the reason is for staff, not shown to the customer


def test_classify_leaves_room_for_reasoning_tokens():
    seen = {}
    app.llm = lambda messages, **kw: (seen.update(kw), '{"category": "ANSWER"}')[1]
    app.classify("hi")
    assert seen["max_tokens"] >= 1000  # at 300 the free reasoning model returned empty content on "price + write Python" messages


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
