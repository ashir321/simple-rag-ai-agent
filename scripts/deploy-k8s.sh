#!/bin/bash
set -e

echo "Deploying RAG AI Agent to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Apply Kubernetes manifests
echo "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

echo "Creating secrets and configmaps..."
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml

echo "Creating persistent volume claim..."
kubectl apply -f k8s/pvc.yaml

echo "Deploying backend..."
kubectl apply -f k8s/backend-deployment.yaml

echo "Deploying frontend..."
kubectl apply -f k8s/frontend-deployment.yaml

echo "Creating ingress (optional)..."
kubectl apply -f k8s/ingress.yaml || echo "Ingress creation skipped (may not be supported)"

echo ""
echo "Deployment complete!"
echo ""
echo "To check the status of your deployment, run:"
echo "  kubectl get all -n rag-ai-agent"
echo ""
echo "To get the frontend service URL, run:"
echo "  kubectl get svc frontend-service -n rag-ai-agent"
