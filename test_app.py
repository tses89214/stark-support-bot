"""`.venv/bin/python test_app.py` — no network, no embedding model. Pins the behaviour the chatbot's safety depends on."""
import os
import sys
import types

os.environ.setdefault("CHAT_MODEL", "test/model")
os.environ.setdefault("OPENROUTER_API_KEY", "test")
fake = types.ModuleType("sentence_transformers")  # app.py loads bge-m3 at import; these tests never embed
fake.SentenceTransformer, fake.util = (lambda *a, **k: None), None
sys.modules["sentence_transformers"] = fake
import app  # must follow the sentence_transformers stub


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


def test_greeting_gets_the_canned_intro_without_retrieval_or_answer_call():
    # "hi" has nothing in the documents; it used to fall through to "I don't know". HELP must answer from code, one classifier call only.
    calls = with_responses([Resp('{"category": "HELP"}')])
    reply, route, sources = app.answer("hi", [])
    assert route == "HELP" and reply == app.REPLIES["HELP"] and sources == [] and len(calls) == 1


def test_handoff_opens_a_ticket_instead_of_saying_i_dont_know():
    # An order-status question cannot be answered from the documents; the customer must reach a human, not get a dead end.
    calls = with_responses([Resp('{"category": "HANDOFF", "reason": "order status"}')])
    app.TICKETS = app.Path("/dev/null")
    reply, route, sources = app.answer("Where is my order #12345?", [])
    assert route == "HANDOFF" and "ticket" in reply and sources == [] and len(calls) == 1


def test_broken_document_pick_is_reported_as_an_error_not_as_not_found():
    # R3 trusts the model to return JSON. If it returns prose, the customer must not be told "not in our documents" (a false claim).
    with_responses([Resp('{"category": "ANSWER"}'), Resp("Let me think about which documents...")])
    reply, route, sources = app.answer("有四人座的嗎", [], "L4", "R3")
    assert route == "ERROR" and reply == app.REPLIES["ERROR"] and sources == []


def test_model_outage_is_reported_as_an_error_and_still_opens_a_ticket():
    # An outage must not be shown as "I passed your complaint to a human" (false) nor as "not in our documents" (false).
    with_responses([Resp(status=500), Resp(status=500)])
    tickets, real = [], app.open_ticket
    app.open_ticket = lambda *a, **k: tickets.append(a) or "t"
    try:
        reply, route, _ = app.answer("How much is the Stark 3?", [])
    finally:
        app.open_ticket = real
    assert route == "ERROR" and reply == app.REPLIES["ERROR"] and len(tickets) == 1  # the human still sees it


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


def test_list_all_question_gets_every_model_doc():
    # top-3 retrieval answered "which models do you sell?" with 3 of 15 and called that the full catalogue
    def fake_llm(messages, **kw):
        system, user = messages[0]["content"], messages[-1]["content"]
        if "how many product documents" in system:
            return '{"scope": "ALL"}' if "全部有哪些" in user else '{"scope": "FEW"}'
        if "final reviewer" in system:
            return '{"ok": true}'
        return '{"category": "ANSWER"}' if "input filter" in system else "reply"

    app.llm = fake_llm
    app.encoder = types.SimpleNamespace(encode=lambda q: q)
    app.util = types.SimpleNamespace(semantic_search=lambda q, v, top_k: [[{"corpus_id": i, "score": 0.9} for i in range(top_k)]])
    _, route, sources = app.answer("全部有哪些？", [])
    assert route == "ANSWER" and len(sources) == sum(n.startswith("model_") for n in app.names)
    _, _, sources = app.answer("How much is the Stark 3?", [])
    assert len(sources) == app.TOP_K  # ordinary questions keep the small prompt


def test_reviewer_rewrites_once_then_blocks_instead_of_releasing_an_unsupported_claim():
    # Stark 8's sheet lists two accessories; a draft saying they "don't affect safety systems" is invented and must not reach the customer
    drafts = iter(["Installing them won't affect the safety systems.", "Still safe, trust us.", "unused"])
    seen = []

    def fake_llm(messages, **kw):
        system = messages[0]["content"]
        if "input filter" in system:
            return '{"category": "ANSWER"}'
        if "how many product documents" in system:
            return '{"scope": "FEW"}'
        if "final reviewer" in system:
            return '{"ok": false, "problems": ["safety claim not in documents"]}'
        seen.append(system)
        return next(drafts)

    app.llm = fake_llm
    app.encoder = types.SimpleNamespace(encode=lambda q: q)
    app.util = types.SimpleNamespace(semantic_search=lambda q, v, top_k: [[{"corpus_id": i, "score": 0.9} for i in range(top_k)]])
    history = []
    reply, route, _ = app.answer("Stark 8 can be modified?", history)
    assert reply == app.REPLIES["UNVERIFIED"] and route == "UNVERIFIED"  # not "not found": the docs may cover it
    assert len(seen) == 2 and "safety claim not in documents" in seen[1]  # exactly one rewrite, told what was wrong
    assert history == []  # a rejected draft must not become context for the next turn

    # the rewrite must not see earlier assistant replies: a claim invented there would be copied into the new draft
    rewrite_inputs = []
    app.llm = lambda messages, **kw: (
        rewrite_inputs.append([m["role"] for m in messages]) if "rejected by a reviewer" in messages[0]["content"] else None
    ) or fake_llm(messages, **kw)
    drafts = iter(["a", "b", "c", "d"])
    app.answer("and the price?", [{"role": "user", "content": "q1"}, {"role": "assistant", "content": "leasing is available"}])
    assert rewrite_inputs and rewrite_inputs[-1].count("assistant") == 0, rewrite_inputs


def test_defense_levels_add_one_thing_each():
    # the demo selector must mirror eval_ladder.py: L0 sends raw text with no rules, L2 fences it, L3 adds the classifier call
    seen = []

    def fake_llm(messages, **kw):
        system = messages[0]["content"]
        seen.append((system, messages[-1]["content"]))
        return '{"category": "ANSWER"}' if "input filter" in system else "reply"

    app.llm = fake_llm
    for level, rules, fenced, classifier in (("L0", False, False, False), ("L1", True, False, False), ("L2", True, True, False), ("L3", True, True, True)):
        seen.clear()
        app.answer("hi", [], level)
        system, user = seen[-1]
        assert ("Answer ONLY" in system) == rules and ("USER INPUT" in user) == fenced, level
        assert any("input filter" in s for s, _ in seen) == classifier, level


def test_retrieval_modes_pick_documents_differently():
    def fake_llm(messages, **kw):
        system = messages[0]["content"]
        return ('{"category": "ANSWER"}' if "input filter" in system else '{"ok": true}' if "final reviewer" in system
                else '{"read": ["model_3", "made_up"]}' if "document index" in system else "reply")

    app.llm = fake_llm
    app.encoder = types.SimpleNamespace(encode=lambda q: q)
    app.util = types.SimpleNamespace(semantic_search=lambda q, v, top_k: [[{"corpus_id": i, "score": 0.9} for i in range(top_k)]])
    assert app.answer("x", [], "L4", "R0")[2] == list(app.names)
    assert len(app.answer("x", [], "L4", "R1")[2]) == app.TOP_K
    assert app.answer("x", [], "L4", "R3")[2] == ["model_3"]  # the invented name is dropped


def test_read_doc_refuses_paths_outside_the_corpus():
    # the document tool is the only door to the corpus: a model-chosen path must not reach .env or other files
    import tempfile
    from pathlib import Path

    import doc_tools

    root = Path(tempfile.mkdtemp())
    (root / "a.txt").write_text("hello")
    (root.parent / "secret.txt").write_text("nope")
    doc_tools.ROOT = root
    assert doc_tools.read_doc("a.txt") == "hello"
    for bad in ("../secret.txt", "/etc/passwd", "../../.env"):
        try:
            doc_tools.read_doc(bad)
        except (ValueError, FileNotFoundError):
            continue
        raise AssertionError(f"read {bad!r}")


def test_throttle_refuses_a_request_that_can_never_fit_the_token_budget():
    # Groq free allows ~8K tokens/minute: an R0 prompt bigger than that must fail loudly, not retry forever or be scored as a wrong answer
    import eval_retrieval_ladder as ladder

    ladder.TPM = 1000
    call = ladder.throttled(lambda messages, **kw: "sent")
    assert call([{"content": "x" * 300}]) == "sent"
    try:
        call([{"content": "x" * 9000}])
    except RuntimeError as e:
        assert "exceeds" in str(e)
    else:
        raise AssertionError("oversize request was sent")
    ladder.TPM = 0


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
