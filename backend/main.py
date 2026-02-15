import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAIError

from rag.pdf_to_text import pdf_to_text
from rag.chunking import chunk_text
from rag.embed_store import build_and_save_index, load_index
from rag.rag_answer import retrieve, generate_answer

app = FastAPI()

# Get allowed origins from environment variable or use defaults
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
PDF_PATH = os.path.join(DATA_DIR, "knowledge.pdf")
INDEX_PATH = os.path.join(DATA_DIR, "index.faiss")
META_PATH = os.path.join(DATA_DIR, "chunks.json")

index = None
chunks = None

class ChatIn(BaseModel):
    message: str

@app.get("/health")
def health():
    """Health check endpoint for Kubernetes probes"""
    return {"status": "healthy"}

@app.get("/")
def root():
    """Root endpoint"""
    return {"message": "RAG AI Agent API", "version": "1.0.0"}

@app.post("/ingest")
def ingest():
    global index, chunks
    try:
        text = pdf_to_text(PDF_PATH)
        chunks = chunk_text(text)
        build_and_save_index(chunks, INDEX_PATH, META_PATH)
        index, chunks = load_index(INDEX_PATH, META_PATH)
        return {"status": "ok", "chunks": len(chunks)}
    except OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during ingestion: {str(e)}")

@app.post("/chat")
def chat(payload: ChatIn):
    global index, chunks

    try:
        if index is None or chunks is None:
            if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
                index, chunks = load_index(INDEX_PATH, META_PATH)
            else:
                return {"answer": "Knowledge base not ingested yet. Call /ingest first."}

        hits = retrieve(payload.message, index, chunks)
        answer = generate_answer(payload.message, hits)
        return {"answer": answer}
    except OpenAIError as e:
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")