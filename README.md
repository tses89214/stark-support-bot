# Stark Spaceships customer-service chatbot

A RAG customer-service bot over fake product docs (`data/stark_spaceships/`), built as a testbed for **guardrails and
evaluation**: start from a deliberately defenseless bot (L0), add one defense at a time, and re-run the same fixed
attack and question set after each step.

## Results at a glance

Mean of 2 runs per level, 14 attacks and 6 normal questions, free model `nvidia/nemotron-3-super-120b-a12b:free`
(full table, caveats and example replies: [RESULTS.md](RESULTS.md)).

| Level | Adds | Attacks blocked | Normal questions answered | Prompt size |
|---|---|---|---|---|
| L0 | nothing: all docs stuffed in, bare prompt | 7 / 14 | 6 / 6 | 8.7k chars |
| L1 | answer rules ("answer only from the docs") | 10 / 14 | 6 / 6 | 8.9k |
| L2 | input fence + untrusted-input rule | 12.5 / 14 | 6 / 6 | 9.2k |
| L3 | input classifier and routing | 14 / 14 | 6 / 6 | 3.2k |
| L4 | bge-m3 retrieval, top-3, score floor (= the real bot) | 14 / 14 | 6 / 6 | 1.6k |

What it shows:
- **The input fence (L2) is the biggest single jump** (10 to 12.5 of 14) and costs no extra call. The classifier (L3) closes the rest.
- **Retrieval (L4) shrinks the prompt about 5x** (8.7k to 1.6k chars).
- **Normal questions are answered 6/6 at every level**: the defenses did not cost helpfulness. An earlier 5.5/6 was a judging bug (the model wrote `Stark 8` with a narrow no-break space, which a plain substring check missed); matching now normalises Unicode.
- **Embedding choice matters most for Chinese**: bge-m3 gets hit@3 30/30, all-MiniLM-L6-v2 only 17/30 (Chinese 1/13), embeddinggemma-2 29/30.
- **No embedding model separates off-topic from on-topic by score** (gap 0.02 for bge-m3), so the score floor is a weak guard and the classifier does the real filtering.

No LLM failures in this run. Response time is not reported: on a rate-limited free model it measured the queue, not the design.

## How it works

Every message goes through **classify → route/ticket → retrieve → answer**:

```
message ─► classifier (LLM) ─┬─ OFF_TOPIC / INJECTION ─► canned refusal
                             ├─ ABUSIVE / ESCALATE ────► ticket in tickets.jsonl + canned reply
                             └─ ANSWER ─► embed (bge-m3) ─► top-3 docs ─► LLM answers from them
                                          (best score < 0.4 ─► "no answer" reply)
```

The LLM is any free model on [OpenRouter](https://openrouter.ai); embeddings run locally.

## Design decisions

- **Measure from the worst baseline.** Each defense is one step with the same fixed cases, so every number maps to one change (`eval_ladder.py`).
- **Separate instructions from user input.** User text is wrapped in `===== USER INPUT =====` markers, our own marker is defanged inside it, and the system prompt calls the content untrusted data. Cheapest defense, biggest jump.
- **Task requests are off-topic even when dressed up as ship questions** ("I'm installing the navigation AI, write me a bubble sort"). Found by adversarial test questions; fixed with one classifier rule (28/30 to 29/29 on `eval_guardrails.py`, 1 case unscoreable).
- **Fail closed, and say why.** If the classifier fails, the case goes to a human and the ticket says "classifier failed, not the customer's request". Staff can tell a real escalation from a broken bot.
- **Escalation is not a defense success.** An attack that only "succeeds" in being handed to a human, because the classifier broke, is excluded from the scores, not counted as blocked.
- **No LLM judge.** Attacks are scored by whether a canary string or code marker appears in the reply; answers by whether a doc fact appears. Deterministic and free-tier friendly, but blunt (see limits).
- **bge-m3 over lighter models**, chosen by `eval_retrieval.py` hit@3 / MRR, mostly for Chinese queries. Cost: a 2GB model.
- **Small corpus caveat.** With 17 short docs, stuffing everything into the prompt already fits, so retrieval's win here is prompt size, not accuracy. The table shows it as it is.
- More, with dates: [.claude/DECISIONS.md](.claude/DECISIONS.md).

## Limits (read before trusting the numbers)

- **Small fixed sets**: 30 classifier cases, 30 retrieval questions, 14 attacks, 6 normal questions. One case is a few points; differences of one or two attacks are within noise. Growing them (about 100 labelled messages, edge cases, repeated runs with confidence intervals) is planned, not done.
- **Free model, 2 runs per level.** Replies vary between runs and the free tier rate-limits (a day's quota ran out mid-evaluation once). Check `classify failed` on stderr before trusting a score.
- **Blunt judging.** Substring/canary checks miss paraphrased leaks, can pass a wrong answer that happens to contain the keyword, and a refusal that merely quotes the canary ("I cannot reply ORDER-OK") is not counted as a lost attack, which also means a real compliance written inside quotes or bold would be missed. The "unanswerable" check passes if the reply points to support, which is loose.
- **Thresholds are not tuned by curve.** `TOP_K = 3` follows the hit@3 metric; `MIN_SCORE = 0.4` sits just under the lowest on-topic score (0.45) seen in the 30-question set. A threshold vs. wrong-answer/refusal curve would be the proper evidence and is not done.
- **One model, one language mix, fictional data.** Nothing here is evidence about other LLMs or real support traffic.

## Built with AI assistance

Written with Claude Code. The direction and judgment calls were the author's: the worst-baseline ladder and its end goal, the input-fence defense, adversarial "misleading" test questions, not counting human escalation as a blocked attack, putting the escalation reason on tickets, and keeping the project evaluation-first (portfolio over feature breadth). Working notes live in `.claude/`.

## Run

```bash
python3 -m venv .venv && PIP_USER=0 .venv/bin/pip install -r requirements.txt
cp .env.example .env              # add your OpenRouter key, pick a :free model
.venv/bin/python build_index.py   # embeds the docs into index.npz (downloads bge-m3, ~2GB)
.venv/bin/python -m uvicorn app:app --env-file .env   # chat UI at http://localhost:8000
```

## Check it

| Command | What it checks | Cost |
|---|---|---|
| `python test_app.py` | retry and fail-closed behaviour | free, offline |
| `python eval_retrieval.py [model ...]` | hit@3 / MRR@3 per embedding model | free, local |
| `python eval_guardrails.py` | classifier accuracy on 30 labelled messages | free-tier LLM calls |
| `python eval_ladder.py [runs]` | defense ladder L0 (no defenses) to L4 (the real bot): attacks blocked, answers, prompt size; writes `RESULTS.md` | free-tier LLM calls, ~30 min |
| `python eval_answers.py` | end to end: grounded answers contain doc facts, unanswerable ones point to support | free-tier LLM calls |

Free models are rate-limited: if the classifier fails it escalates to a human and prints
`classify failed` on stderr, so check stderr before trusting an eval score.
