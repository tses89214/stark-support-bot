# promptfoo: attack sample generation

Generates extra attack prompts for the bot with [promptfoo](https://www.promptfoo.dev) (MIT, pinned 0.124.1). The ladder in `eval_ladder.py`
stays our own; promptfoo only drafts candidate attacks, which are reviewed by hand before they join the fixed set
(`../eval_candidates_attacks.jsonl`, all `unreviewed`).

```bash
set -a; . ../.env; set +a
./run.sh redteam generate -c promptfooconfig.yaml -o attacks.yaml --no-cache   # needs the bot running for the target URL only when you run an eval
```

`run.sh` sets `PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true` plus telemetry, update-check and sharing off. By default promptfoo
generates and grades through its own server and sends the app description, prompts and replies there
([data handling](https://www.promptfoo.dev/docs/red-team/troubleshooting/data-handling)); here generation runs on our own OpenRouter model.

Findings from the first run (2026-10-13):
- Offline works for `prompt-extraction`, `debug-access` and custom `policy` plugins (5 prompts each).
- The `hijacking` plugin (off-topic tasks, the most relevant one for this bot) refuses to run without remote generation. It is not used; turning remote on is a decision for the owner, because it sends data out.
- The free reasoning model leaks its own thinking into some prompts ("Make sure each line starts with..."): 9 of 20 were flagged as probably junk. This is why generated samples need review before they count.
