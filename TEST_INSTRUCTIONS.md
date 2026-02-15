# Testing Instructions for Policy Query Fix

## Issue Fixed
The application was showing "Error contacting server" when asking about policy details due to:
1. Invalid OpenAI model name: `gpt-5.2` (changed to `gpt-4o-mini`)
2. Incorrect API method: `client.responses.create()` (changed to `client.chat.completions.create()`)
3. Wrong response parsing: `response.output_text` (changed to `response.choices[0].message.content`)

## Vector Database Information
This project uses **FAISS (Facebook AI Similarity Search)** as documented in the README.md.
- Location: `backend/rag/embed_store.py`
- Storage: `backend/data/index.faiss` and `backend/data/chunks.json`
- Embedding Model: OpenAI `text-embedding-3-small`

## Testing the Fix

### Prerequisites
1. Python 3.9+
2. Node.js 18+
3. Valid OpenAI API key

### Setup Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your OpenAI API key
cat > .env << EOF
OPENAI_API_KEY=your-actual-openai-api-key-here
ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
EOF

# Start the backend server
uvicorn main:app --reload --port 8000
```

### Ingest Knowledge Base

In a new terminal:

```bash
curl -X POST http://localhost:8000/ingest
```

Expected output:
```json
{"status":"ok","chunks":N}
```

### Setup Frontend

In a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the URL shown (usually http://localhost:5173)

### Test the Chat

1. Open the frontend in your browser
2. Click on the chat widget
3. Ask questions like:
   - "What is the policy about?"
   - "How do I file a claim?"
   - "What is a deductible?"

**Expected Result**: You should receive proper answers from the AI assistant instead of "Error contacting server."

### Direct API Testing

You can also test the backend API directly:

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How do I file a claim?"}'
```

Expected response:
```json
{
  "answer": "To file a claim, you can call our claims line or submit through the portal."
}
```

## Verification Checklist

- [ ] Backend starts without errors
- [ ] `/ingest` endpoint successfully processes the PDF
- [ ] `/chat` endpoint returns answers (not error messages)
- [ ] Frontend chat widget displays AI responses
- [ ] No "Error contacting server" messages appear
- [ ] Answers are relevant to the policy document

## Troubleshooting

### "Error contacting server" still appears
- Check that the backend is running on port 8000
- Verify CORS is configured correctly (ALLOWED_ORIGINS in .env)
- Check browser console for network errors
- Verify OpenAI API key is valid and has credits

### "Knowledge base not ingested yet"
- Run the `/ingest` endpoint first
- Check that `backend/data/knowledge.pdf` exists
- Verify `backend/data/index.faiss` and `backend/data/chunks.json` were created

### OpenAI API errors
- Verify your API key is correct
- Check you have sufficient credits
- Ensure you have access to `gpt-4o-mini` model
- Check rate limits if making many requests
