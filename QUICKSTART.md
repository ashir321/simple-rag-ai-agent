# Quick Start Guide - RAG AI Agent K8s Deployment

Get the RAG AI Agent running in Kubernetes in 5 minutes!

## Prerequisites

- Docker
- Kubernetes cluster (minikube, kind, or cloud)
- kubectl configured
- OpenAI API key

## Option 1: Local Testing with Docker Compose (Easiest)

```bash
# 1. Set your API key
export OPENAI_API_KEY=sk-your-key-here

# 2. Start everything
docker-compose up --build

# 3. Wait for services to start, then open browser
# Frontend: http://localhost
# Backend: http://localhost:8000

# 4. Ingest knowledge base
curl -X POST http://localhost:8000/ingest

# 5. Start chatting in the browser!
```

## Option 2: Minikube (Local K8s)

```bash
# 1. Start minikube
minikube start

# 2. Build images in minikube
eval $(minikube docker-env)
./scripts/build-images.sh

# 3. Configure your API key
# Edit k8s/secrets.yaml and replace 'your-openai-api-key-here'

# 4. Deploy
./scripts/deploy-k8s.sh

# 5. Wait for pods to be ready
kubectl get pods -n rag-ai-agent -w

# 6. Access the app
minikube service frontend-service -n rag-ai-agent

# 7. Ingest knowledge base
kubectl port-forward -n rag-ai-agent svc/backend-service 8000:8000
# In another terminal:
curl -X POST http://localhost:8000/ingest
```

## Option 3: Kind (K8s in Docker)

```bash
# 1. Create cluster
kind create cluster --name rag-ai-agent

# 2. Build and load images
./scripts/build-images.sh
kind load docker-image rag-ai-agent-backend:latest --name rag-ai-agent
kind load docker-image rag-ai-agent-frontend:latest --name rag-ai-agent

# 3. Configure API key (edit k8s/secrets.yaml)

# 4. Deploy
./scripts/deploy-k8s.sh

# 5. Access via port forward
kubectl port-forward -n rag-ai-agent svc/frontend-service 8080:80
# Open http://localhost:8080

# 6. Ingest knowledge base
kubectl port-forward -n rag-ai-agent svc/backend-service 8000:8000
curl -X POST http://localhost:8000/ingest
```

## Option 4: Cloud (GKE, EKS, AKS)

```bash
# 1. Connect to your cluster
# GKE: gcloud container clusters get-credentials CLUSTER_NAME
# EKS: aws eks update-kubeconfig --name CLUSTER_NAME
# AKS: az aks get-credentials --resource-group RG --name CLUSTER_NAME

# 2. Build and push images to your registry
./scripts/build-images.sh
docker tag rag-ai-agent-backend:latest YOUR_REGISTRY/rag-ai-agent-backend:latest
docker tag rag-ai-agent-frontend:latest YOUR_REGISTRY/rag-ai-agent-frontend:latest
docker push YOUR_REGISTRY/rag-ai-agent-backend:latest
docker push YOUR_REGISTRY/rag-ai-agent-frontend:latest

# 3. Update deployment YAML files with your registry images

# 4. Configure API key and CORS
# Edit k8s/secrets.yaml with your OpenAI API key
# Edit k8s/configmap.yaml with your actual domain for CORS

# 5. Deploy
./scripts/deploy-k8s.sh

# 6. Get external IP
kubectl get svc frontend-service -n rag-ai-agent
# Wait for EXTERNAL-IP to be assigned

# 7. Update CORS with external IP/domain
# Edit k8s/configmap.yaml: ALLOWED_ORIGINS: "http://YOUR-EXTERNAL-IP"
kubectl apply -f k8s/configmap.yaml
kubectl rollout restart deployment/backend -n rag-ai-agent

# 8. Access via external IP
# Open http://EXTERNAL-IP in browser

# 9. Ingest knowledge base
curl -X POST http://EXTERNAL-IP:8000/ingest
```

## Verify Deployment

```bash
# Check all resources
kubectl get all -n rag-ai-agent

# Check pod status
kubectl get pods -n rag-ai-agent

# View backend logs
kubectl logs -n rag-ai-agent deployment/backend

# View frontend logs
kubectl logs -n rag-ai-agent deployment/frontend

# Test backend health
kubectl port-forward -n rag-ai-agent svc/backend-service 8000:8000
curl http://localhost:8000/health
```

## Common Issues

### Pods Not Starting

```bash
kubectl describe pod -n rag-ai-agent <pod-name>
kubectl logs -n rag-ai-agent <pod-name>
```

### Can't Access Application

```bash
# For minikube, use:
minikube service frontend-service -n rag-ai-agent

# For others, use port forwarding:
kubectl port-forward -n rag-ai-agent svc/frontend-service 8080:80
```

### Image Pull Errors

For local clusters (minikube/kind), make sure:
- Images are built in the cluster's Docker daemon
- imagePullPolicy is set to IfNotPresent

## Cleanup

```bash
# Remove everything
./scripts/cleanup-k8s.sh

# For minikube
minikube stop
minikube delete

# For kind
kind delete cluster --name rag-ai-agent
```

## Next Steps

- Read [KUBERNETES.md](KUBERNETES.md) for detailed deployment guide
- Read [TESTING.md](TESTING.md) for testing procedures
- Read [k8s/README.md](k8s/README.md) for manifest documentation
- Configure SSL/TLS for production
- Set up monitoring and logging
- Configure autoscaling
- Implement backup strategy

## Support

For issues or questions:
1. Check the logs: `kubectl logs -n rag-ai-agent deployment/backend`
2. Review [KUBERNETES.md](KUBERNETES.md) troubleshooting section
3. Check pod status: `kubectl describe pod -n rag-ai-agent <pod-name>`

## Architecture Overview

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Browser   │─────▶│  Frontend   │─────▶│   Backend   │
│             │      │   (Nginx)   │      │  (FastAPI)  │
└─────────────┘      └─────────────┘      └─────────────┘
                                                   │
                                                   │
                                          ┌────────▼────────┐
                                          │ Persistent Vol  │
                                          │ (FAISS + Data)  │
                                          └─────────────────┘
```

Happy deploying! 🚀
