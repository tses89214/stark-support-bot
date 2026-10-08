"""Offline step: embed every product doc into index.npz. Re-run when data/stark_spaceships changes."""
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DOCS_DIR = Path("data/stark_spaceships")
INDEX = Path("index.npz")

if __name__ == "__main__":
    paths = sorted(DOCS_DIR.glob("*.txt"))
    vectors = SentenceTransformer(EMBED_MODEL).encode([p.read_text() for p in paths])
    np.savez(INDEX, names=[p.stem for p in paths], vectors=vectors)
    print(f"indexed {len(paths)} docs -> {INDEX}")
