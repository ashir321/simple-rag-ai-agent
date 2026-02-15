# Quick Fix Guide - "Unable to contact the server" Error in Kubernetes

## TL;DR

If you're getting "Unable to contact the server" error in Kubernetes:

```bash
# 1. Rebuild the frontend image with the fix
cd /path/to/simple-rag-ai-agent
./scripts/build-images.sh

# 2. Redeploy to Kubernetes
./scripts/deploy-k8s.sh

# 3. Wait for pods to be ready
kubectl get pods -n rag-ai-agent -w
```

The frontend will now use relative URLs that properly route through the nginx proxy to the backend.

## What Was Fixed

**Before**: Frontend was hardcoded to connect to `http://localhost:8000`
- ❌ Doesn't work in Kubernetes (localhost is not the backend)
- ❌ Bypasses nginx proxy entirely

**After**: Frontend uses relative URLs (`/chat`)
- ✅ Works in Kubernetes
- ✅ Routes through nginx proxy
- ✅ Nginx forwards to backend service

## Architecture

```
User Browser
    ↓
    ↓ Request to /chat
    ↓
Nginx Proxy (nginx-proxy-service)
    ↓
    ↓ Proxies to backend-service:8000
    ↓
Backend Service
    ↓
Backend Pod (FastAPI)
```

## Files Changed

1. `frontend/Dockerfile` - Accepts VITE_BACKEND_URL build argument
2. `scripts/build-images.sh` - Passes empty VITE_BACKEND_URL when building
3. `frontend/src/ChatWidget.jsx` - Properly handles empty vs undefined URLs
4. Documentation files

## Need More Help?

See the comprehensive guide: [docs/K8S_CONNECTION_TROUBLESHOOTING.md](K8S_CONNECTION_TROUBLESHOOTING.md)
