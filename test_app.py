"""`.venv/bin/python test_app.py` — no network, no embedding model. Pins the behaviour the chatbot's safety depends on."""
import os
import sys
import types

os.environ.setdefault("CHAT_MODEL", "test/model")
os.environ.setdefault("OPENROUTER_API_KEY", "test")
fake = types.ModuleType("sentence_transformers")  # app.py loads bge-m3 at import; these tests never embed
fake.SentenceTransformer, fake.util = (lambda *a, **k: None), None
sys.modules["sentence_transformers"] = fake
import app  # noqa: E402


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
    assert app.classify("How much is the Stark 3?") == "ESCALATE"


def test_classify_unknown_category_escalates():
    with_responses([Resp('{"category": "MAKE_UP_SOMETHING"}')])
    assert app.classify("hi") == "ESCALATE"


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
