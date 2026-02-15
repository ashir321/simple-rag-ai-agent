# Kubernetes Deployment Guide

This guide will help you deploy the RAG AI Agent to a Kubernetes cluster.

## Prerequisites

- Docker installed (for building images)
- Kubernetes cluster (local with minikube/kind, or cloud-based like GKE, EKS, AKS)
- kubectl configured to connect to your cluster
- OpenAI API key

## Quick Start

### 1. Build Docker Images

```bash
./scripts/build-images.sh
```

This will build both the backend and frontend Docker images. The frontend image is built with an empty `VITE_BACKEND_URL` so it uses relative URLs, allowing the nginx proxy to route traffic correctly in Kubernetes.

### 2. Configure Secrets

Edit `k8s/secrets.yaml` and replace `your-openai-api-key-here` with your actual OpenAI API key:

```yaml
stringData:
  OPENAI_API_KEY: "sk-your-actual-key-here"
```

**Important:** Never commit your actual API key to version control!

### 3. Deploy to Kubernetes

```bash
./scripts/deploy-k8s.sh
```

This will:
- Create the `rag-ai-agent` namespace
- Deploy all necessary resources (secrets, configmaps, pvcs, deployments, services)
- Set up nginx proxy loadbalancer for external access

### 4. Check Deployment Status

```bash
kubectl get all -n rag-ai-agent
```

Wait until all pods are in `Running` state.

### 5. Access the Application

#### Option A: Using Nginx Proxy LoadBalancer (Recommended)

Get the external IP:
```bash
kubectl get svc nginx-proxy-service -n rag-ai-agent
```

Access the app at `http://<EXTERNAL-IP>`

The nginx proxy will route:
- `/` → Frontend
- `/api` → Backend API
- `/health` → Backend health check
- `/ingest` → Backend ingest endpoint

#### Option B: Using Port Forward (Local development)

Frontend:
```bash
kubectl port-forward -n rag-ai-agent svc/frontend-service 8080:80
```
Access at: http://localhost:8080

Backend:
```bash
kubectl port-forward -n rag-ai-agent svc/backend-service 8000:8000
```
Access at: http://localhost:8000

Nginx Proxy (to test locally):
```bash
kubectl port-forward -n rag-ai-agent svc/nginx-proxy-service 8080:80
```
Access at: http://localhost:8080

### 6. Initialize the Knowledge Base

Before using the chat, you need to ingest the PDF:

```bash
# Port forward the backend if not already done
kubectl port-forward -n rag-ai-agent svc/backend-service 8000:8000

# In another terminal, ingest the PDF
curl -X POST http://localhost:8000/ingest
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │              rag-ai-agent namespace              │   │
│  │                                                   │   │
│  │  ┌──────────────┐                                │   │
│  │  │ Nginx Proxy  │                                │   │
│  │  │  LoadBalancer│                                │   │
│  │  │  Replicas: 2 │                                │   │
│  │  └──────┬───────┘                                │   │
│  │         │                                         │   │
│  │         ├─────────────────┬───────────────────┐  │   │
│  │         │                 │                   │  │   │
│  │  ┌──────▼──────┐   ┌──────▼──────┐          │  │   │
│  │  │   Frontend  │   │   Backend   │          │  │   │
│  │  │  Deployment │   │  Deployment │          │  │   │
│  │  │  (Nginx)    │   │  (FastAPI)  │          │  │   │
│  │  │  Replicas:2 │   │  Replicas:1 │          │  │   │
│  │  └──────┬──────┘   └──────┬──────┘          │  │   │
│  │         │                 │                   │  │   │
│  │  ┌──────▼──────┐   ┌──────▼──────┐          │  │   │
│  │  │  Frontend   │   │   Backend   │          │  │   │
│  │  │   Service   │   │   Service   │          │  │   │
│  │  │ (ClusterIP) │   │ (ClusterIP) │          │  │   │
│  │  └─────────────┘   └──────┬──────┘          │  │   │
│  │                            │                   │  │   │
│  │                    ┌───────▼────────┐         │  │   │
│  │                    │ PersistentVolume│         │  │   │
│  │                    │   (Data/FAISS)  │         │  │   │
│  │                    └─────────────────┘         │  │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────┘
```

## Configuration

### Backend Configuration

Configuration is managed via:
- **Secrets** (`k8s/secrets.yaml`): Sensitive data like API keys
- **ConfigMap** (`k8s/configmap.yaml`): Application configuration

### Frontend Configuration

The frontend is built at Docker build time. To change the backend URL for production:

1. Update the build args in `k8s/frontend-deployment.yaml` or `docker-compose.yml`
2. Rebuild the frontend image

### Resource Limits

Default resource limits:

**Backend:**
- Requests: 512Mi memory, 250m CPU
- Limits: 1Gi memory, 500m CPU

**Frontend:**
- Requests: 128Mi memory, 100m CPU
- Limits: 256Mi memory, 200m CPU

Adjust in the respective deployment YAML files based on your needs.

### Persistent Storage

Backend uses a PersistentVolumeClaim (PVC) for storing:
- FAISS vector index
- PDF metadata
- Uploaded PDFs

Default storage: 1Gi (adjust in `k8s/pvc.yaml` if needed)

## Scaling

### Scale Frontend

```bash
kubectl scale deployment frontend -n rag-ai-agent --replicas=3
```

### Scale Backend

**Note:** Currently, the backend uses in-memory state for the FAISS index. For production multi-replica deployment, consider:
1. Using a shared persistent volume (ReadWriteMany)
2. Implementing a caching layer (Redis)
3. Loading the index on startup from persistent storage

```bash
kubectl scale deployment backend -n rag-ai-agent --replicas=2
```

## Monitoring

### View Logs

Backend logs:
```bash
kubectl logs -f -n rag-ai-agent deployment/backend
```

Frontend logs:
```bash
kubectl logs -f -n rag-ai-agent deployment/frontend
```

### Health Checks

Both services have health checks configured:

Backend: `http://<backend-service>:8000/health`
Frontend: `http://<frontend-service>/`

## Troubleshooting

### Pods not starting

```bash
kubectl describe pod -n rag-ai-agent <pod-name>
kubectl logs -n rag-ai-agent <pod-name>
```

### Backend can't connect to OpenAI

1. Verify the secret is correctly set:
   ```bash
   kubectl get secret backend-secrets -n rag-ai-agent -o yaml
   ```
2. Check backend logs for API errors

### Frontend can't connect to backend

If you see the error "Unable to contact the server. Please check your connection and try again.", see the detailed [K8S Connection Troubleshooting Guide](docs/K8S_CONNECTION_TROUBLESHOOTING.md).

Quick checks:

1. **Verify backend service is running:**
   ```bash
   kubectl get svc backend-service -n rag-ai-agent
   kubectl get pods -n rag-ai-agent -l app=backend
   ```

2. **Check nginx proxy is routing correctly:**
   ```bash
   # Check nginx proxy logs
   kubectl logs -n rag-ai-agent deployment/nginx-proxy
   
   # Test backend health through nginx proxy
   kubectl port-forward -n rag-ai-agent svc/nginx-proxy-service 8080:80
   # In another terminal:
   curl http://localhost:8080/health
   ```

3. **Ensure frontend image was built with empty VITE_BACKEND_URL:**
   - The frontend must be built with `--build-arg VITE_BACKEND_URL=""` to use relative URLs
   - This is automatically done by `./scripts/build-images.sh`
   - If you built the image manually, rebuild it with the correct build arg

4. **Check CORS configuration in backend ConfigMap:**
   ```bash
   kubectl get configmap backend-config -n rag-ai-agent -o yaml
   ```

### Persistent volume issues

```bash
kubectl get pvc -n rag-ai-agent
kubectl describe pvc backend-data-pvc -n rag-ai-agent
```

### Nginx 504 Gateway Timeout errors

If you experience 504 Gateway Timeout errors, see the [Nginx Timeout Fix Guide](docs/NGINX_TIMEOUT_FIX.md) for detailed troubleshooting steps.

Quick check:
```bash
# Check nginx proxy logs
kubectl logs -n rag-ai-agent deployment/nginx-proxy

# Verify nginx configuration
kubectl exec -n rag-ai-agent deployment/nginx-proxy -- nginx -t

# Restart nginx if needed
kubectl rollout restart deployment/nginx-proxy -n rag-ai-agent
```

## Cleanup

To remove all resources:

```bash
./scripts/cleanup-k8s.sh
```

Or manually:

```bash
kubectl delete namespace rag-ai-agent
```

## Production Considerations

1. **SSL/TLS**: Enable HTTPS using cert-manager and Let's Encrypt
2. **Secrets Management**: Use external secrets management (AWS Secrets Manager, HashiCorp Vault)
3. **Monitoring**: Set up Prometheus and Grafana for metrics
4. **Logging**: Configure centralized logging (ELK stack, Loki)
5. **Backups**: Regular backups of the persistent volume
6. **Autoscaling**: Configure HorizontalPodAutoscaler for automatic scaling
7. **Network Policies**: Implement network policies for security
8. **Resource Quotas**: Set namespace resource quotas

## Local Development with Minikube

```bash
# Start minikube
minikube start

# Build images directly in minikube
eval $(minikube docker-env)
./scripts/build-images.sh

# Deploy
./scripts/deploy-k8s.sh

# Get the service URL
minikube service nginx-proxy-service -n rag-ai-agent
```

## Using with Kind (Kubernetes in Docker)

```bash
# Create cluster
kind create cluster --name rag-ai-agent

# Load images into kind
kind load docker-image rag-ai-agent-backend:latest --name rag-ai-agent
kind load docker-image rag-ai-agent-frontend:latest --name rag-ai-agent

# Deploy
./scripts/deploy-k8s.sh

# Port forward to access
kubectl port-forward -n rag-ai-agent svc/nginx-proxy-service 8080:80
```

## Cloud Provider Specific Notes

### Google Kubernetes Engine (GKE)

```bash
# Create cluster
gcloud container clusters create rag-ai-agent \
  --num-nodes=2 \
  --machine-type=e2-medium

# Push images to GCR
docker tag rag-ai-agent-backend:latest gcr.io/PROJECT-ID/rag-ai-agent-backend:latest
docker tag rag-ai-agent-frontend:latest gcr.io/PROJECT-ID/rag-ai-agent-frontend:latest
docker push gcr.io/PROJECT-ID/rag-ai-agent-backend:latest
docker push gcr.io/PROJECT-ID/rag-ai-agent-frontend:latest

# Update image names in deployment YAML files
# Deploy as usual
```

### Amazon EKS

```bash
# Create cluster
eksctl create cluster --name rag-ai-agent --region us-west-2 --nodes 2

# Push images to ECR
aws ecr create-repository --repository-name rag-ai-agent-backend
aws ecr create-repository --repository-name rag-ai-agent-frontend
# Tag and push images...

# Deploy as usual
```

### Azure AKS

```bash
# Create cluster
az aks create --resource-group myResourceGroup \
  --name rag-ai-agent --node-count 2

# Push images to ACR
az acr create --resource-group myResourceGroup --name myACR --sku Basic
az acr login --name myACR
# Tag and push images...

# Deploy as usual
```
