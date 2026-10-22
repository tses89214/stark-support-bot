"""Read-only document tools. Every access to the corpus goes through these, so each read shows up as a TOOL span in MLflow.
Tracing is on only when MLFLOW_TRACKING_URI is set (e.g. sqlite:///data/runtime/mlflow.db); without it `trace` does nothing and mlflow is not imported."""

import os
from pathlib import Path

import numpy as np

from backend.build_index import EMBED_MODEL

if os.environ.get("MLFLOW_TRACKING_URI"):
    import mlflow

    def trace(span_type="TOOL"):
        return lambda fn: mlflow.trace(fn, span_type=span_type)

    def record_usage(usage):
        """Put the provider's token counts on the current span; MLflow sums them per trace (Traces tab, token usage)."""
        span = mlflow.get_current_active_span()
        if span and usage:
            span.set_attribute(
                "mlflow.chat.tokenUsage",
                {
                    "input_tokens": usage.get("prompt_tokens", 0),
                    "output_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
            )

    def update_trace_session(session):
        mlflow.update_current_trace(metadata={"mlflow.trace.session": session})

    def current_trace_id():
        span = mlflow.get_current_active_span()
        return span.trace_id if span else ""
else:

    def trace(span_type="TOOL"):
        return lambda fn: fn

    def update_trace_session(session):
        pass

    def current_trace_id():
        return ""

    def record_usage(usage):
        pass


ROOT = Path("data/stark_scaled")
encoder = None  # set by the caller to share one bge-m3 copy (2GB); built lazily otherwise
_vectors = {}  # corpus root -> (paths, embeddings)


def list_docs():
    return sorted(str(p.relative_to(ROOT)) for p in ROOT.rglob("*.txt"))


@trace()
def read_index():
    return (ROOT / "INDEX.md").read_text()


@trace()
def read_doc(path):
    """Read-only by construction: nothing here writes, and a path outside ROOT is refused."""
    full = (ROOT / path).resolve()
    if not full.is_relative_to(ROOT.resolve()) or full.suffix != ".txt":
        raise ValueError(f"not a corpus document: {path!r}")
    return full.read_text()


@trace()
def search_docs(query, k=3):
    """Paths of the k documents closest to the query (bge-m3 cosine)."""
    global encoder
    from sentence_transformers import SentenceTransformer, util

    encoder = encoder or SentenceTransformer(EMBED_MODEL)
    if ROOT not in _vectors:
        cache = ROOT / "index.npz"  # regenerated corpus dir drops this, so the cache cannot go stale
        if cache.exists():
            data = np.load(cache)
            _vectors[ROOT] = (list(data["paths"]), data["vectors"])
        else:
            paths = list_docs()
            vectors = encoder.encode([read_doc(p) for p in paths])
            np.savez(cache, paths=paths, vectors=vectors)
            _vectors[ROOT] = (paths, vectors)
    paths, vectors = _vectors[ROOT]
    hits = util.semantic_search(encoder.encode(query), vectors, top_k=k)[0]
    return [paths[h["corpus_id"]] for h in hits]
