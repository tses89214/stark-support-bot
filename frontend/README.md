# frontend/

`index.html` is the whole chat UI (one page, no build step). `backend/app.py` serves it at `/` (http://localhost:8000); it sends a session id and one message per turn.
