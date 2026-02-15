#!/bin/bash
set -e

echo "Removing RAG AI Agent from Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Delete all resources in namespace
echo "Deleting all resources..."
kubectl delete -f k8s/ingress.yaml --ignore-not-found=true
kubectl delete -f k8s/frontend-deployment.yaml --ignore-not-found=true
kubectl delete -f k8s/backend-deployment.yaml --ignore-not-found=true
kubectl delete -f k8s/pvc.yaml --ignore-not-found=true
kubectl delete -f k8s/configmap.yaml --ignore-not-found=true
kubectl delete -f k8s/secrets.yaml --ignore-not-found=true
kubectl delete -f k8s/namespace.yaml --ignore-not-found=true

echo ""
echo "Cleanup complete!"
