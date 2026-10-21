"""Server-side conversations: one row per turn, so the browser cannot forge the history and a ticket can point at its session and trace.
ponytail: a local SQLite file, no expiry; swap in Redis/Postgres and a TTL if this ever serves real traffic."""
import json
import os
import sqlite3
import threading
import time

DB = os.environ.get("SESSIONS_DB", "data/runtime/sessions.db")
if DB != ":memory:":
    os.makedirs(os.path.dirname(DB), exist_ok=True)
_db = sqlite3.connect(DB, check_same_thread=False)
_db.row_factory = sqlite3.Row
_db.execute("""create table if not exists turns (session text, n integer, ts text, user text, reply text, route text,
               sources text, question text, focus text, ticket text, trace_id text, primary key (session, n))""")
_lock = threading.Lock()


def turns(session):
    """Every stored turn of a session, oldest first, JSON columns decoded."""
    with _lock:
        rows = _db.execute("select * from turns where session = ? order by n", (session,)).fetchall()
    return [{**r, "sources": json.loads(r["sources"]), "focus": json.loads(r["focus"])} for r in map(dict, rows)]


def add(session, user, reply, route, sources=(), question="", focus=(), ticket="", trace_id=""):
    with _lock:
        n = _db.execute("select count(*) from turns where session = ?", (session,)).fetchone()[0]
        _db.execute("insert into turns values (?,?,?,?,?,?,?,?,?,?,?)",
                    (session, n, time.strftime("%Y-%m-%dT%H:%M:%S"), user, reply, route, json.dumps(list(sources)),
                     question, json.dumps(list(focus)), ticket, trace_id))
        _db.commit()


def history(session):
    """What the prompts may see: answered turns only, as chat messages, plus the models in focus after the last one."""
    answered = [t for t in turns(session) if t["route"] == "ANSWER"]
    msgs = [m for t in answered for m in ({"role": "user", "content": t["user"]}, {"role": "assistant", "content": t["reply"]})]
    return msgs, (answered[-1]["focus"] if answered else [])
