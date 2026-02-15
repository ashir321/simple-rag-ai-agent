import json
import numpy as np
import faiss
from openai import OpenAI, OpenAIError

client = OpenAI()
EMBED_MODEL = "text-embedding-3-small"

def embed_texts(texts):
    try:
        resp = client.embeddings.create(model=EMBED_MODEL, input=texts)
        vectors = [d.embedding for d in resp.data]
        arr = np.array(vectors, dtype="float32")
        faiss.normalize_L2(arr)
        return arr
    except OpenAIError as e:
        raise OpenAIError(f"Failed to generate embeddings: {str(e)}") from e

def build_and_save_index(chunks, index_path, meta_path):
    vectors = embed_texts(chunks)
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    faiss.write_index(index, index_path)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks}, f, ensure_ascii=False, indent=2)

def load_index(index_path, meta_path):
    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return index, meta["chunks"]