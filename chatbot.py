"""Stark Spaceships customer-service chatbot: answers only from data/stark_spaceships/."""
import os
from pathlib import Path

from openai import OpenAI
from sentence_transformers import SentenceTransformer, util

TOP_K = 3
SYSTEM = (
    "You are a customer service chatbot for Stark Spaceships. "
    "Answer ONLY from the documents below. If they don't contain the answer, "
    "say you don't know and suggest contacting customer_service@stack_spaceship.com. "
    "Mention the model name you rely on.\n\nDocuments:\n{docs}"
)

# reads OPENAI_API_KEY and OPENAI_BASE_URL, so any OpenAI-compatible endpoint (e.g. a LiteLLM gateway) works
client = OpenAI()
MODEL = os.environ.get("CHAT_MODEL", "gpt-4o")
encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
# ponytail: one doc = one chunk, in-memory embeddings; add chunking + vector DB when corpus outgrows RAM
docs = {p.stem: p.read_text() for p in sorted(Path("data/stark_spaceships").glob("*.txt"))}
names = list(docs)
doc_emb = encoder.encode(list(docs.values()), convert_to_tensor=True)


def retrieve(query, top_k=TOP_K):
    hits = util.semantic_search(encoder.encode(query, convert_to_tensor=True), doc_emb, top_k=top_k)[0]
    return [names[h["corpus_id"]] for h in hits]


def answer(query, history):
    sources = retrieve(query)
    system = SYSTEM.format(docs="\n".join(docs[n] for n in sources))
    reply = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}, *history, {"role": "user", "content": query}],
    ).choices[0].message.content
    history += [{"role": "user", "content": query}, {"role": "assistant", "content": reply}]
    return reply, sources


if __name__ == "__main__":
    history = []
    while (q := input("You: ").strip()) not in ("", "quit", "exit"):
        reply, sources = answer(q, history)
        print(f"Bot: {reply}\n[sources: {', '.join(sources)}]\n")
