# Build a RAG AI Agent in 30 Minutes

A complete end-to-end project to build a **Retrieval-Augmented Generation (RAG) AI chatbot** using your own PDF knowledge base and embed it as a chat widget on a website.

This project includes:

* FastAPI backend (PDF → chunks → embeddings → vector search → AI answer)
* React frontend chat widget
* Sample PDF generator
* FAISS vector database
* OpenAI Responses API integration

---

## Features

* Ask questions directly from your PDF documents
* No hallucinations, answers are generated only from retrieved context
* Clean backend architecture
* Lightweight frontend widget
* Works for insurance, SaaS docs, policies, HR, legal, internal tools, etc.

---

## Project Structure

```
simple-rag-bot/
  backend/
    main.py
    requirements.txt
    rag/
      pdf_to_text.py
      chunking.py
      embed_store.py
      rag_answer.py
      make_sample_pdf.py
    data/
      knowledge.pdf

  frontend/
    package.json
    index.html
    src/
      main.jsx
      App.jsx
      ChatWidget.jsx
```

---

## Tech Stack

### Backend

* FastAPI
* PyPDF
* tiktoken
* FAISS
* NumPy
* OpenAI Python SDK
* ReportLab

### Frontend

* React
* Vite

---

## Requirements

* Python 3.9+
* Node.js 18+
* OpenAI API key

---

## Environment Setup (.env)

Create a file named `.env` inside the `backend` folder:

```
backend/.env
```

Add your OpenAI API key:

```
OPENAI_API_KEY=your_api_key_here
```

Make sure this file is **not committed to GitHub**. Add it to `.gitignore`.

---

## Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Generate sample PDF

```bash
python rag/make_sample_pdf.py
```

### Run server

```bash
uvicorn main:app --reload --port 8000
```

### Ingest PDF (build vector index)

```bash
curl -X POST http://localhost:8000/ingest
```

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown in terminal (usually [http://localhost:5173](http://localhost:5173))

Click the chat widget and start asking questions.

---

## Example Question

```
How do I file a claim?
```

The bot will:

1. Search the PDF knowledge base
2. Retrieve the most relevant chunks
3. Generate a safe answer from those chunks only

## How RAG Works (Simple)

```
PDF → Text → Chunks → Embeddings → Vector DB → Retrieval → AI Answer
```

This ensures:

* Accurate answers
* Domain-specific responses
* No hallucinations

## Production Tips

* Store multiple PDFs
* Add citations to show answer sources
* Add conversation memory
* Add user authentication
* Add human support handoff
* Use a persistent database (Pinecone, Weaviate, or PostgreSQL with pgvector)

---

## Common Issue

**OpenAI Limit**
If you hit rate limits or token limits, consider:
* Using other providers (e.g., Gemini)

## License

MIT – free to use, modify, and ship.

---

## Kubernetes Deployment

This project is now **Kubernetes-ready**! 🚀

### Quick K8s Deployment

```bash
# 1. Build Docker images
./scripts/build-images.sh

# 2. Configure your OpenAI API key in k8s/secrets.yaml

# 3. Deploy to Kubernetes
./scripts/deploy-k8s.sh

# 4. Access the application
kubectl port-forward -n rag-ai-agent svc/frontend-service 8080:80
```

### Docker Compose (Local Testing)

```bash
# Set your OpenAI API key
export OPENAI_API_KEY=your-key-here

# Run with Docker Compose
docker-compose up --build
```

### Documentation

For complete Kubernetes deployment guide, see [KUBERNETES.md](KUBERNETES.md)

Includes:
- Complete deployment instructions
- Cloud provider setup (GKE, EKS, AKS)
- Scaling and monitoring
- Troubleshooting
- Production best practices

---

## Credits

Built as a clean educational RAG reference project.

Happy building.
