# Fix for "Unable to contact the server" Error

## Problem
When running the application with `docker-compose up`, the chat functionality would fail with the error:
```
Unable to contact the server. Please check your connection and try again.
```

## Root Cause
The frontend was configured to connect to `http://localhost:8000` at build time. This doesn't work when the frontend runs in a Docker container because:
- The browser loads the frontend from the container
- When the browser tries to connect to `localhost:8000`, it's trying to connect to the user's machine, not the backend container
- The backend container is only accessible via Docker's internal network as `http://backend:8000`

## Solution
We implemented an nginx reverse proxy pattern (matching the Kubernetes setup) where:
1. The frontend's nginx server proxies API requests to the backend
2. The frontend code uses relative URLs in production mode
3. All API calls (`/chat`, `/ingest`, `/health`) are proxied through nginx to the backend container

## How It Works Now

### In Docker Compose (Production)
```
Browser → http://localhost/chat → nginx (frontend container) → http://backend:8000/chat → Backend
```

### In Local Development (npm run dev)
```
Browser → http://localhost:8000/chat → Backend directly
```

## Files Changed
1. **frontend/nginx.conf** - Added proxy configuration for API endpoints
2. **frontend/src/ChatWidget.jsx** - Smart URL handling (relative in prod, localhost in dev)
3. **docker-compose.yml** - Removed hardcoded backend URL, updated CORS
4. **frontend/.env.example** - Updated documentation

## Testing the Fix

### Using Docker Compose
```bash
# 1. Set your OpenAI API key
export OPENAI_API_KEY=your-key-here

# 2. Start the services
docker-compose up --build

# 3. Wait for services to start (check logs for "Application startup complete")

# 4. Ingest the knowledge base
curl -X POST http://localhost:8000/ingest

# 5. Open http://localhost in your browser

# 6. Try searching - it should now work!
```

### Using Local Development
```bash
# Terminal 1 - Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python rag/make_sample_pdf.py
uvicorn main:app --reload

# Terminal 2 - Ingest
curl -X POST http://localhost:8000/ingest

# Terminal 3 - Frontend
cd frontend
npm install
npm run dev

# Open http://localhost:5173 in your browser
```

## Benefits
✅ Works in Docker Compose  
✅ Works in local development  
✅ Consistent with Kubernetes deployment  
✅ No breaking changes  
✅ Better architecture (proxy pattern)  

## Troubleshooting

### Still seeing the error?
1. Make sure both containers are running:
   ```bash
   docker-compose ps
   ```

2. Check backend logs:
   ```bash
   docker-compose logs backend
   ```

3. Check frontend logs:
   ```bash
   docker-compose logs frontend
   ```

4. Verify the backend is healthy:
   ```bash
   curl http://localhost:8000/health
   ```

5. Make sure you've ingested the knowledge base:
   ```bash
   curl -X POST http://localhost:8000/ingest
   ```

### Port already in use?
If port 80 or 8000 is already in use, you can modify the ports in `docker-compose.yml`:
```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Use 8001 instead of 8000
  frontend:
    ports:
      - "8080:80"    # Use 8080 instead of 80
```

Then access at `http://localhost:8080` and update the ingest command:
```bash
curl -X POST http://localhost:8001/ingest
```
