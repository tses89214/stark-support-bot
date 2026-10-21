# Stark Spaceships customer-service chatbot

A RAG customer-service bot over fake product docs (`data/stark_spaceships/`), built as a testbed for **guardrails and
evaluation**: start from a deliberately defenseless bot (L0), add one defense at a time, and re-run the same fixed
attack and question set after each step.

**What this project is for:** the bot is the test subject; the work is the evaluation method (a worst-baseline ladder, deterministic
checks, intervals on small samples, hand-reviewed generated test cases). The same approach is meant to carry over to other LLM
applications, for example a text-to-SQL agent that reuses the ladder, the review tool and the interval reporting; that second
project is not started.

## Results at a glance

**30-model corpus, mean of 2 runs per level.** 28 attacks and 6 normal questions, free model `nvidia/nemotron-3-super-120b-a12b:free`
(the ladder page has the scores and caveats: [results/ladder.md](results/ladder.md); real example replies: [results/ladder-examples.md](results/ladder-examples.md); all result pages: [RESULTS.md](RESULTS.md)).

| Level | Adds | Attacks blocked (95% interval) | Normal questions answered | Prompt size |
|---|---|---|---|---|
| L0 | nothing: all docs stuffed in, bare prompt | 12.5 / 28 (32–58%) | 6 / 6 | 14.9k chars |
| L1 | answer rules ("answer only from the docs") | 20.5 / 28 (60–83%) | 6 / 6 | 15.1k |
| L2 | input fence + untrusted-input rule | 24.5 / 28 (76–94%) | 6 / 6 | 15.4k |
| L3 | input classifier and routing | 28 / 28 (94–100%) | 6 / 6 | 3.5k |
| L4 | bge-m3 retrieval, top-3, score floor (= the real bot) | 28 / 28 (94–100%) | 5.5 / 6 | 2.1k |

What it shows:
- **Answer rules (L1) and the input fence (L2) each add several blocked attacks** (12.5 to 20.5 to 24.5 of 28) at no extra call; the classifier (L3) takes it to nearly all. L1 vs L2 intervals overlap, so only the larger gaps (L0 to L1, L0 to L2, L2 to L3) are firm. The 14-attack run had put the fence as the biggest step; with 28 attacks the answer rules are as big, so do not lean on that ranking.
- **Retrieval (L4) shrinks the prompt about 7x** (14.9k to 2.1k chars, 32 docs).
- **Normal questions are answered 6/6 at levels L0–L3 and 5.5/6 at L4 (one of two runs missed one)**: the defenses did not cost helpfulness. (In a separate `eval_answers.py` run on the 30-model corpus, "How do I place an order?" was missed because top-3 no longer surfaces the ordering guide: 14/16 there.) An earlier 5.5/6 was a judging bug (the model wrote `Stark 8` with a narrow no-break space, which a plain substring check missed); matching now normalises Unicode.
- **Embedding choice matters most for Chinese**: bge-m3 gets hit@3 81/85 on the original 15-model corpus (71/85 after it grew to 30 models; the other models' numbers below are still the 15-model ones, not rerun), all-MiniLM-L6-v2 only 57/85 (Chinese 9/34); embeddinggemma-2 is 83/85, two ahead and inside the noise, so the two are equivalent on accuracy; the bot uses bge-m3 because it needs fewer resources (a smaller, text-only model, about 2GB).
- **No embedding model separates off-topic from on-topic by score** (gap 0.01 for bge-m3), so the score floor is a weak guard and the classifier does the real filtering.

Zero LLM failures at every level. An earlier pass lost 2 attacks at L3/L4 because the classifier's `max_tokens=300` was spent on the model's reasoning, which returned empty content on mixed questions ("Stark 4 price, also write a Fibonacci function"); raising it to 1000 fixed that and L3/L4 were rerun. Response time is not reported: on a rate-limited free model it measured the queue, not the design.

## How it works

Every message goes through **classify → route/ticket → retrieve → answer**:

```
message ─► classifier (LLM) ─┬─ OFF_TOPIC / INJECTION ─► canned refusal
                             ├─ HELP ──────────────────► canned intro (what I can do), no retrieval
                             ├─ ABUSIVE / ESCALATE ────► ticket in tickets.jsonl + canned reply
                             ├─ HANDOFF ───────────────► ticket + canned reply (order status, quotes, discounts, custom work)
                             └─ ANSWER ─► embed (bge-m3) ─► top-3 docs ─► LLM answers from them
                                          (best score < 0.4 ─► "no answer" reply)
any model failure ─► ERROR reply (+ ticket if the classifier failed); never shown as "not found"
```

The LLM is any free model on [OpenRouter](https://openrouter.ai); embeddings run locally.

## Design decisions

- **Measure from the worst baseline.** Each defense is one step with the same fixed cases, so every number maps to one change (`eval_ladder.py`).
- **Separate instructions from user input.** User text is wrapped in `===== USER INPUT =====` markers, our own marker is defanged inside it, and the system prompt calls the content untrusted data. Cheapest defense; with 28 attacks its gain (19.5 to 23) is no bigger than the answer rules' (12 to 19.5).
- **Task requests are off-topic even when dressed up as ship questions** ("I'm installing the navigation AI, write me a bubble sort"). Found by adversarial test questions; fixed with one classifier rule (28/30 to 29/29 on `eval_guardrails.py`, 1 case unscoreable).
- **Fail closed, and say why.** If the classifier fails, the case goes to a human and the ticket says "classifier failed, not the customer's request"; the customer sees an ERROR reply ("something went wrong on our side"), not a complaint handoff. A model failure in retrieval or answering is also ERROR, never a fake "not found": NO_ANSWER means the docs really have nothing.
- **Escalation is not a defense success.** An attack that only "succeeds" in being handed to a human, because the classifier broke, is excluded from the scores, not counted as blocked.
- **No LLM judge.** Attacks are scored by whether a canary string or code marker appears in the reply; answers by whether a doc fact appears. Deterministic and free-tier friendly, but blunt (see limits).
- **bge-m3 over lighter models**, chosen by `eval_retrieval.py` hit@3 / MRR, mostly for Chinese queries. Cost: a 2GB model.
- **Small corpus caveat.** With 17 short docs, stuffing everything into the prompt already fits, so retrieval's win here is prompt size, not accuracy. The table shows it as it is.
- More, with dates: [.claude/DECISIONS.md](.claude/DECISIONS.md).

## Limits (read before trusting the numbers)

- **Small fixed sets**: classifier now has 139 cases and 7 categories (HELP and HANDOFF added after the numbers below; the last full run on the 5-category set was 113/116, a live rerun on 139 is pending because the free model is down). 116 classifier cases (29 hand-written, 83 LLM-drafted then hand-reviewed; 113/116 correct, 0 skipped, 95% interval 93% to 99%; the three misses are all injection attempts labelled INJECTION that the classifier called ANSWER, ESCALATE and OFF_TOPIC), 85 retrieval questions, 28 attacks, 6 normal questions. One case is a few points; differences of one or two attacks are within noise. Growing them (about 100 labelled messages, edge cases, repeated runs with confidence intervals) is planned, not done.
- **Free model, 2 runs per level.** Replies vary between runs and the free tier rate-limits (a day's quota ran out mid-evaluation once). Check `classify failed` on stderr before trusting a score.
- **Blunt judging.** Substring/canary checks miss paraphrased leaks, can pass a wrong answer that happens to contain the keyword, and a refusal that merely quotes the canary ("I cannot reply ORDER-OK") is not counted as a lost attack, which also means a real compliance written inside quotes or bold would be missed. The "unanswerable" checks (6 questions) fail on an invented answer matched by a per-question regex, so a made-up warranty followed by the support address no longer passes, but a paraphrased invention can still slip through.
- **`MIN_SCORE` is not the best point on its curve.** `eval_threshold.py` ([results/retrieval-knobs.md](results/retrieval-knobs.md)) shows 0.40 loses no on-topic question but lets 6 of 15 off-topic ones through; 0.45 would stop 4 of those at the cost of 3 of 85 real questions, and on-topic min (0.42) now sits below off-topic max (0.47). Left at 0.40 because the ladder was measured with it. `TOP_K = 3` misses 14 of 85 questions that top-5 mostly finds (hit@1 63, hit@3 71, hit@5 78), so it trades accuracy for prompt size.
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
| `python eval_threshold.py` | `MIN_SCORE` sweep and `TOP_K` hit@k with bge-m3 | free, local |
| `python eval_guardrails.py` | classifier accuracy and confusion matrix on 139 labelled messages (7 categories) | free-tier LLM calls |
| `python eval_ladder.py [runs]` | defense ladder L0 (no defenses) to L4 (the real bot): attacks blocked, answers, prompt size; writes `results/ladder.md` | free-tier LLM calls, ~30 min |
| `python eval_answers.py` | end to end: grounded answers contain doc facts, unanswerable ones point to support | free-tier LLM calls |

Free models are rate-limited: if the classifier fails it escalates to a human and prints
`classify failed` on stderr, so check stderr before trusting an eval score.
