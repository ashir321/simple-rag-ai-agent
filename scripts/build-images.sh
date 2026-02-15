#!/bin/bash
set -e

echo "Building Docker images for RAG AI Agent..."

# Build backend image
echo "Building backend image..."
docker build -t ashiruddinsk/rag-ai-agent-backend:latest ./backend

# Build frontend image  
echo "Building frontend image..."
docker build -t ashiruddinsk/rag-ai-agent-frontend:latest ./frontend

echo "Docker images built successfully!"
echo ""
echo "Available images:"
docker images | grep rag-ai-agent

echo "Docker images push DockerHub successfully!"
echo ""
docker push ashiruddinsk/rag-ai-agent-backend:latest
docker push ashiruddinsk/rag-ai-agent-frontend:latest
