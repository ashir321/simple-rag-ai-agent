# Testing Guide

This guide helps you test the Kubernetes deployment locally and in production.

## Prerequisites

- Docker installed
- Docker Compose (for local testing)
- kubectl (for K8s deployment)
- A Kubernetes cluster (minikube, kind, or cloud-based)

## Local Testing with Docker Compose

### 1. Set Environment Variables

```bash
export OPENAI_API_KEY=your-openai-api-key-here
```

### 2. Start Services

```bash
docker-compose up --build
```

This will:
- Build both backend and frontend Docker images
- Start both services
- Backend will be available at http://localhost:8000
- Frontend will be available at http://localhost:80

### 3. Generate Sample PDF (if needed)

If you want to generate a new sample PDF:

```bash
cd backend
python rag/make_sample_pdf.py
```

### 4. Ingest the Knowledge Base

```bash
curl -X POST http://localhost:8000/ingest
```

### 5. Test the Application

Open http://localhost in your browser and try asking questions like:
- "How do I file a claim?"
- "What is covered by the policy?"

### 6. Test Backend Health

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}

curl http://localhost:8000/
# Should return API info
```

### 7. Stop Services

```bash
docker-compose down
```

To remove volumes as well:
```bash
docker-compose down -v
```

## Testing with Minikube

### 1. Start Minikube

```bash
minikube start --cpus=2 --memory=4096
```

### 2. Build Images in Minikube

```bash
# Point Docker to Minikube's Docker daemon
eval $(minikube docker-env)

# Build images
./scripts/build-images.sh
```

### 3. Deploy to Minikube

```bash
# Update secret with your API key first!
# Edit k8s/secrets.yaml

# Deploy
./scripts/deploy-k8s.sh
```

### 4. Check Deployment Status

```bash
kubectl get all -n rag-ai-agent

# Watch pods start up
kubectl get pods -n rag-ai-agent -w
```

### 5. Access the Application

```bash
# Get the service URL
minikube service frontend-service -n rag-ai-agent

# Or use port forwarding
kubectl port-forward -n rag-ai-agent svc/frontend-service 8080:80
# Access at http://localhost:8080
```

### 6. Ingest Knowledge Base

```bash
# Port forward backend
kubectl port-forward -n rag-ai-agent svc/backend-service 8000:8000

# In another terminal
curl -X POST http://localhost:8000/ingest
```

### 7. View Logs

```bash
# Backend logs
kubectl logs -n rag-ai-agent deployment/backend -f

# Frontend logs
kubectl logs -n rag-ai-agent deployment/frontend -f
```

### 8. Cleanup

```bash
./scripts/cleanup-k8s.sh

# Stop minikube
minikube stop
```

## Testing with Kind

### 1. Create Cluster

```bash
kind create cluster --name rag-ai-agent
```

### 2. Build and Load Images

```bash
# Build images
./scripts/build-images.sh

# Load into kind
kind load docker-image rag-ai-agent-backend:latest --name rag-ai-agent
kind load docker-image rag-ai-agent-frontend:latest --name rag-ai-agent
```

### 3. Deploy and Test

```bash
# Deploy
./scripts/deploy-k8s.sh

# Port forward to access
kubectl port-forward -n rag-ai-agent svc/frontend-service 8080:80
kubectl port-forward -n rag-ai-agent svc/backend-service 8000:8000

# Test as usual
```

### 4. Cleanup

```bash
kind delete cluster --name rag-ai-agent
```

## Automated Testing

### Test Script

Create a test script to verify the deployment:

```bash
#!/bin/bash
# test-deployment.sh

set -e

echo "Testing backend health..."
curl -f http://localhost:8000/health || exit 1

echo "Testing backend API..."
curl -f http://localhost:8000/ || exit 1

echo "Testing ingestion..."
curl -f -X POST http://localhost:8000/ingest || exit 1

echo "Testing chat endpoint..."
curl -f -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"How do I file a claim?"}' || exit 1

echo "All tests passed!"
```

### Run Tests

```bash
chmod +x test-deployment.sh
./test-deployment.sh
```

## Performance Testing

### Load Testing with Apache Bench

```bash
# Test backend health endpoint
ab -n 1000 -c 10 http://localhost:8000/health

# Test chat endpoint
ab -n 100 -c 5 -p test-payload.json -T application/json http://localhost:8000/chat
```

Create `test-payload.json`:
```json
{"message":"How do I file a claim?"}
```

### Stress Testing

```bash
# Install hey (HTTP load generator)
go install github.com/rakyll/hey@latest

# Test with hey
hey -n 1000 -c 50 http://localhost:8000/health
```

## Troubleshooting Common Issues

### Issue: Backend Pod Not Starting

```bash
# Check pod status
kubectl describe pod -n rag-ai-agent <backend-pod-name>

# Check logs
kubectl logs -n rag-ai-agent <backend-pod-name>

# Common causes:
# 1. Missing OpenAI API key
# 2. Image pull issues
# 3. Resource constraints
```

### Issue: Frontend Can't Connect to Backend

```bash
# Verify backend service is running
kubectl get svc -n rag-ai-agent backend-service

# Check CORS configuration
kubectl get configmap -n rag-ai-agent backend-config -o yaml

# Test backend from within cluster
kubectl run -i --tty --rm debug --image=curlimages/curl --restart=Never -n rag-ai-agent -- curl http://backend-service:8000/health
```

### Issue: PVC Not Binding

```bash
# Check PVC status
kubectl get pvc -n rag-ai-agent

# Check storage classes
kubectl get storageclass

# For minikube, ensure storage provisioner is enabled
minikube addons enable storage-provisioner
```

### Issue: Image Not Found

```bash
# For minikube
eval $(minikube docker-env)
docker images | grep rag-ai-agent

# For kind
kind load docker-image rag-ai-agent-backend:latest --name rag-ai-agent
kind load docker-image rag-ai-agent-frontend:latest --name rag-ai-agent
```

## Validation Checklist

Before deploying to production:

- [ ] Docker images build successfully
- [ ] Backend container starts and responds to health checks
- [ ] Frontend container serves the application
- [ ] Backend can connect to OpenAI API
- [ ] PDF ingestion works correctly
- [ ] Chat functionality returns valid responses
- [ ] All K8s manifests are valid YAML
- [ ] Resource limits are appropriate
- [ ] Persistent volume is working
- [ ] Health checks are configured correctly
- [ ] CORS is configured for production domains
- [ ] Secrets are properly secured (not committed to git)
- [ ] Logs are accessible
- [ ] Services are accessible via LoadBalancer/Ingress

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/test.yml`:

```yaml
name: Test K8s Deployment

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Backend Image
      run: docker build -t rag-ai-agent-backend:latest ./backend
    
    - name: Build Frontend Image
      run: docker build -t rag-ai-agent-frontend:latest ./frontend
    
    - name: Validate K8s Manifests
      run: |
        pip install yamllint
        yamllint k8s/
    
    - name: Test with Kind
      uses: helm/kind-action@v1
      with:
        cluster_name: test-cluster
    
    - name: Load Images into Kind
      run: |
        kind load docker-image rag-ai-agent-backend:latest --name test-cluster
        kind load docker-image rag-ai-agent-frontend:latest --name test-cluster
    
    - name: Deploy to Kind
      run: ./scripts/deploy-k8s.sh
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    
    - name: Wait for Pods
      run: kubectl wait --for=condition=ready pod -l app=backend -n rag-ai-agent --timeout=300s
    
    - name: Test Deployment
      run: |
        kubectl port-forward -n rag-ai-agent svc/backend-service 8000:8000 &
        sleep 5
        curl -f http://localhost:8000/health
```

## Monitoring in Production

### Basic Monitoring

```bash
# Watch pods
watch kubectl get pods -n rag-ai-agent

# Watch resources
kubectl top pods -n rag-ai-agent
kubectl top nodes

# Check events
kubectl get events -n rag-ai-agent --sort-by='.lastTimestamp'
```

### Advanced Monitoring

For production, consider setting up:
- Prometheus for metrics
- Grafana for dashboards
- ELK/EFK stack for logs
- Jaeger for distributed tracing

## Security Testing

### Check for Vulnerabilities

```bash
# Scan Docker images
docker scan rag-ai-agent-backend:latest
docker scan rag-ai-agent-frontend:latest

# Check K8s security
kubectl auth can-i --list -n rag-ai-agent
```

### Secret Management

```bash
# Verify secrets are not exposed
kubectl get secret backend-secrets -n rag-ai-agent -o json | jq '.data | map_values(@base64d)'

# Consider using external secret management in production
```
