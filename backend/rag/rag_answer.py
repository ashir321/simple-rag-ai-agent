import numpy as np
from openai import OpenAI, OpenAIError
import faiss

client = OpenAI()
CHAT_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"

def embed_query(query: str):
    try:
        resp = client.embeddings.create(model=EMBED_MODEL, input=[query])
        vec = np.array([resp.data[0].embedding], dtype="float32")
        faiss.normalize_L2(vec)
        return vec
    except OpenAIError as e:
        raise OpenAIError(f"Failed to generate embedding: {str(e)}") from e

def retrieve(query, index, chunks, k=4):
    qvec = embed_query(query)
    scores, ids = index.search(qvec, k)
    results = []
    for i in ids[0]:
        if i != -1:
            results.append(chunks[i])
    return results

def generate_answer(user_question, retrieved_chunks):
    context = "\n\n".join(retrieved_chunks)

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an Insurance Agency Customer Care assistant. "
                        "Use only the provided context to answer. "
                        "If not found, say you don't have it and offer human support."
                    )
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion:\n{user_question}"
                }
            ]
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        raise OpenAIError(f"Failed to generate answer: {str(e)}") from e