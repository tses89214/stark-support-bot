"""Server-side conversations: one row per turn, so the browser cannot forge the history and a ticket can point at its session and trace.
ponytail: a local SQLite file, no expiry; swap in Redis/Postgres and a TTL if this ever serves real traffic."""
import json
import os
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass, field

DB = os.environ.get("SESSIONS_DB", "data/runtime/sessions.db")
if DB != ":memory:":
    os.makedirs(os.path.dirname(DB), exist_ok=True)
_db = sqlite3.connect(DB, check_same_thread=False)
_db.row_factory = sqlite3.Row
_db.execute("""create table if not exists turns (session text, n integer, ts text, user text, reply text, route text,
               sources text, question text, focus text, ticket text, trace_id text, primary key (session, n))""")
_lock = threading.Lock()


@dataclass
class Focus:
    """Where the conversation stands, filled in again on every turn and kept by the server (never by the browser or the answer prompt):
    later steps use it to resolve 'it' / 'that one' without asking a model to remember."""
    talking_about: list = field(default_factory=list)  # Stark models the latest question is about, e.g. ["Stark 1"]
    interested_in: str = ""  # the one model the customer said they like or want to order; "" until they choose
    goal: str = ""  # what the customer is trying to do, in a few words ("choose a small honeymoon ship"); only read by the filter prompts

    def __bool__(self):
        return bool(self.talking_about or self.interested_in or self.goal)

    def lines(self):
        """The focus as prompt lines for the filter steps."""
        return "".join(f"\n{label}: {value}" for label, value in (
            ("Models in focus", ", ".join(self.talking_about)), ("Customer is interested in", self.interested_in), ("Customer's goal", self.goal)) if value)

    def after(self, route, models, seen):
        """The focus after this turn. `models` = Stark models found in the standalone question; `seen` = what the classifier read from the
        conversation. Blocked turns (off-topic, injection, abuse) do not steer the conversation: they keep the focus as it was."""
        if route in ("OFF_TOPIC", "INJECTION", "ABUSIVE"):
            return self
        return Focus(models or self.talking_about, seen.get("interested_in") or self.interested_in, seen.get("goal") or self.goal)

    @staticmethod
    def load(text):
        """From the stored JSON; rows written before this class existed hold a bare list of models."""
        data = json.loads(text)
        return Focus(list(data)) if isinstance(data, list) else Focus(**data)


def turns(session):
    """Every stored turn of a session, oldest first, JSON columns decoded."""
    with _lock:
        rows = _db.execute("select * from turns where session = ? order by n", (session,)).fetchall()
    return [{**r, "sources": json.loads(r["sources"]), "focus": Focus.load(r["focus"])} for r in map(dict, rows)]


def add(session, user, reply, route, sources=(), question="", focus=None, ticket="", trace_id=""):
    """Store one finished turn (any route, also blocked and failed ones) as the next row of the session."""
    with _lock:
        n = _db.execute("select count(*) from turns where session = ?", (session,)).fetchone()[0]
        _db.execute("insert into turns values (?,?,?,?,?,?,?,?,?,?,?)",
                    (session, n, time.strftime("%Y-%m-%dT%H:%M:%S"), user, reply, route, json.dumps(list(sources)),
                     question, json.dumps(asdict(focus or Focus())), ticket, trace_id))
        _db.commit()


def history(session):
    """What the prompts may see: answered turns only, as chat messages, plus the latest non-empty Focus."""
    answered = [t for t in turns(session) if t["route"] == "ANSWER"]
    msgs = [m for t in answered for m in ({"role": "user", "content": t["user"]}, {"role": "assistant", "content": t["reply"]})]
    return msgs, next((t["focus"] for t in reversed(turns(session)) if t["focus"]), Focus())  # any route: a greeting still carries the focus forward
