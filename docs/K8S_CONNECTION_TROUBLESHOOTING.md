# Kubernetes Connection Troubleshooting Guide

## Problem: "Unable to contact the server" Error

If you see the error message "Unable to contact the server. Please check your connection and try again." when using the application in Kubernetes, this guide will help you resolve it.

## Root Cause

The frontend application needs to know how to reach the backend API. In Kubernetes deployments with an nginx proxy:
- The frontend should use **relative URLs** (e.g., `/chat`) so requests go through the nginx proxy
- The nginx proxy then routes these requests to the backend service
- If the frontend is configured with an absolute URL like `http://localhost:8000`, it will try to connect directly to localhost, which fails in Kubernetes

## Solution

The fix involves building the frontend Docker image with an empty `VITE_BACKEND_URL` environment variable:

### 1. Build Images with the Correct Configuration

Use the provided build script which automatically sets the correct build argument:

```bash
./scripts/build-images.sh
```

This script builds the frontend with `--build-arg VITE_BACKEND_URL=""`, which tells the frontend to use relative URLs.

### 2. Push Images to Registry (if needed)

If you're using a container registry, the build script also pushes the images:

```bash
# Already done by build-images.sh
docker push ashiruddinsk/rag-ai-agent-backend:latest
docker push ashiruddinsk/rag-ai-agent-frontend:latest
```

### 3. Deploy to Kubernetes

```bash
./scripts/deploy-k8s.sh
```

### 4. Verify the Fix

After deployment, test that the frontend can communicate with the backend:

```bash
# Port forward to the nginx proxy
kubectl port-forward -n rag-ai-agent svc/nginx-proxy-service 8080:80

# In another terminal, test the connection
curl http://localhost:8080/health

# Access the application
# Open browser to http://localhost:8080
```

## Manual Build (If Not Using Scripts)

If you need to build the frontend image manually:

```bash
cd frontend
docker build --build-arg VITE_BACKEND_URL="" -t your-registry/frontend:latest .
docker push your-registry/frontend:latest
```

## How It Works

1. **Build Time**: The `VITE_BACKEND_URL` build argument is passed to Docker
2. **Vite Build**: During `npm run build`, Vite embeds this value in the compiled JavaScript
3. **Runtime**: The frontend code checks if `VITE_BACKEND_URL` is defined:
   - If empty string: Uses relative URLs (`/chat`)
   - If undefined: Defaults to `http://localhost:8000` (for local development)
4. **Nginx Routing**: Nginx proxy receives requests to `/chat` and routes them to `backend-service:8000`

## Architecture Diagram

```
Browser → Nginx Proxy (port 80)
           ↓
           ├─→ / → Frontend Service (static files)
           └─→ /chat → Backend Service (API)
```

## Verification Checklist

- [ ] Frontend image built with `--build-arg VITE_BACKEND_URL=""`
- [ ] Nginx proxy deployment is running
- [ ] Backend service is running
- [ ] All pods are in `Running` state
- [ ] Nginx proxy can reach backend service

```bash
# Check all resources
kubectl get all -n rag-ai-agent

# Check nginx can reach backend
kubectl exec -n rag-ai-agent deployment/nginx-proxy -- wget -O- http://backend-service:8000/health
```

## Still Having Issues?

1. **Check nginx proxy logs:**
   ```bash
   kubectl logs -n rag-ai-agent deployment/nginx-proxy
   ```

2. **Check backend logs:**
   ```bash
   kubectl logs -n rag-ai-agent deployment/backend
   ```

3. **Verify nginx configuration:**
   ```bash
   kubectl exec -n rag-ai-agent deployment/nginx-proxy -- nginx -t
   ```

4. **Test backend health directly:**
   ```bash
   kubectl port-forward -n rag-ai-agent svc/backend-service 8000:8000
   curl http://localhost:8000/health
   ```

5. **Check if frontend has the correct build:**
   - The frontend container should have been built with the empty VITE_BACKEND_URL
   - Rebuilding and redeploying may be necessary if the old image is cached

## For Local Development

If you're developing locally and want the frontend to connect directly to the backend:

1. Create a `.env` file in the `frontend` directory:
   ```bash
   VITE_BACKEND_URL=http://localhost:8000
   ```

2. Start development server:
   ```bash
   cd frontend
   npm run dev
   ```

This configuration is different from production/k8s where relative URLs are used.
