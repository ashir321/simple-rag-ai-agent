# Kubernetes Manifests

This directory contains all Kubernetes manifests for deploying the RAG AI Agent.

## Files Overview

### Core Resources

- **`namespace.yaml`** - Creates the `rag-ai-agent` namespace for isolating resources
- **`secrets.yaml`** - Stores sensitive data (OpenAI API key)
- **`configmap.yaml`** - Application configuration (CORS settings, etc.)
- **`pvc.yaml`** - Persistent Volume Claim for storing FAISS index and data

### Application Deployments

- **`backend-deployment.yaml`** - FastAPI backend deployment and service
  - Deployment with 1 replica
  - ClusterIP service on port 8000
  - Health checks configured
  - Resource limits: 512Mi-1Gi memory, 250m-500m CPU
  
- **`frontend-deployment.yaml`** - React frontend deployment and service
  - Deployment with 2 replicas
  - LoadBalancer service on port 80
  - Health checks configured
  - Resource limits: 128Mi-256Mi memory, 100m-200m CPU

### Optional Resources

- **`ingress.yaml`** - Ingress configuration for external access
  - Routes traffic to frontend and backend
  - Supports SSL/TLS with cert-manager (commented out)

## Deployment Order

The manifests should be applied in this order:

1. Namespace
2. Secrets and ConfigMaps
3. Persistent Volume Claims
4. Deployments and Services
5. Ingress (optional)

The deployment script `scripts/deploy-k8s.sh` handles this automatically.

## Configuration

### Before Deploying

#### 1. Update Secrets

Edit `secrets.yaml` and replace the placeholder with your actual OpenAI API key:

```yaml
stringData:
  OPENAI_API_KEY: "sk-your-actual-key-here"
```

**Important:** Never commit your actual API key to version control!

#### 2. Update ConfigMap (Optional)

Edit `configmap.yaml` to add your production domains to CORS:

```yaml
data:
  ALLOWED_ORIGINS: "https://your-domain.com,https://www.your-domain.com"
```

#### 3. Update Ingress (Optional)

If using Ingress, edit `ingress.yaml`:

```yaml
spec:
  rules:
  - host: your-domain.com  # Change this
```

### Resource Customization

#### Adjust Replicas

In `backend-deployment.yaml` or `frontend-deployment.yaml`:

```yaml
spec:
  replicas: 3  # Change as needed
```

#### Adjust Resources

In the deployment files, modify resource requests/limits:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "1Gi"
    cpu: "500m"
```

#### Adjust Storage

In `pvc.yaml`, change the storage size:

```yaml
resources:
  requests:
    storage: 5Gi  # Increase as needed
```

## Service Types

### Backend Service (ClusterIP)

The backend uses ClusterIP, making it only accessible within the cluster:

```yaml
spec:
  type: ClusterIP
```

To access it externally during development:
```bash
kubectl port-forward -n rag-ai-agent svc/backend-service 8000:8000
```

### Frontend Service (LoadBalancer)

The frontend uses LoadBalancer to get an external IP:

```yaml
spec:
  type: LoadBalancer
```

Alternatives:
- **NodePort** - For on-premise or testing
- **ClusterIP** - If using Ingress only

Change in `frontend-deployment.yaml` if needed.

## Environment Variables

### Backend Environment Variables

Set in deployment via secrets and configmaps:

- `OPENAI_API_KEY` - From secret
- `ALLOWED_ORIGINS` - From configmap

To add more environment variables:

1. Add to `configmap.yaml` or `secrets.yaml`
2. Reference in `backend-deployment.yaml`:

```yaml
env:
- name: NEW_VAR
  valueFrom:
    configMapKeyRef:
      name: backend-config
      key: NEW_VAR
```

## Health Checks

### Liveness Probe

Checks if the container is alive:

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Readiness Probe

Checks if the container is ready to serve traffic:

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

Adjust these values based on your application's startup time and requirements.

## Persistent Storage

The backend uses a PersistentVolumeClaim to store:
- FAISS vector index
- Chunk metadata
- PDF files

### Storage Classes

The PVC uses the `standard` storage class by default:

```yaml
storageClassName: standard
```

Available storage classes vary by cluster:
- **minikube**: `standard`
- **GKE**: `standard`, `standard-rwo`
- **EKS**: `gp2`, `gp3`
- **AKS**: `default`, `managed-premium`

Check available classes:
```bash
kubectl get storageclass
```

### Access Modes

Currently configured as `ReadWriteOnce` (single node):

```yaml
accessModes:
  - ReadWriteOnce
```

For multi-node deployments with multiple backend replicas, consider:
- Using a shared file system (ReadWriteMany)
- Network storage (NFS, EFS, etc.)
- Caching layer (Redis)

## Ingress Configuration

### Prerequisites

Requires an Ingress controller (e.g., nginx-ingress, traefik):

```bash
# For minikube
minikube addons enable ingress

# For other clusters, install nginx-ingress
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.1/deploy/static/provider/cloud/deploy.yaml
```

### Path Routing

The Ingress routes requests to different services:

- `/` → Frontend service
- `/api` → Backend service

Update your frontend to use `/api` prefix when deployed with Ingress.

### SSL/TLS

To enable HTTPS:

1. Install cert-manager:
```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
```

2. Create a ClusterIssuer for Let's Encrypt

3. Uncomment the TLS sections in `ingress.yaml`

## Scaling

### Manual Scaling

```bash
# Scale backend
kubectl scale deployment backend -n rag-ai-agent --replicas=3

# Scale frontend
kubectl scale deployment frontend -n rag-ai-agent --replicas=5
```

### Auto-scaling

Create a HorizontalPodAutoscaler:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: rag-ai-agent
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 1
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 80
```

Apply:
```bash
kubectl apply -f hpa.yaml
```

## Security Considerations

### Network Policies

Add network policies to restrict traffic:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: backend-policy
  namespace: rag-ai-agent
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8000
```

### Pod Security

Add security context to deployments:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000
  readOnlyRootFilesystem: true
```

### Secrets Management

For production, use external secret management:
- AWS Secrets Manager
- Azure Key Vault
- HashiCorp Vault
- Google Secret Manager

## Backup and Recovery

### Backup PVC Data

```bash
# Create a backup pod
kubectl run backup -n rag-ai-agent --image=busybox --rm -it --restart=Never \
  --overrides='{"spec":{"volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"backend-data-pvc"}}],"containers":[{"name":"backup","image":"busybox","command":["tar","czf","/tmp/backup.tar.gz","/data"],"volumeMounts":[{"name":"data","mountPath":"/data"}]}]}}'

# Copy backup out
kubectl cp rag-ai-agent/backup:/tmp/backup.tar.gz ./backup.tar.gz
```

### Restore from Backup

```bash
# Create restore pod
kubectl run restore -n rag-ai-agent --image=busybox --rm -it --restart=Never \
  --overrides='{"spec":{"volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"backend-data-pvc"}}],"containers":[{"name":"restore","image":"busybox","volumeMounts":[{"name":"data","mountPath":"/data"}],"command":["sh"]}]}}'

# In the pod
tar xzf /tmp/backup.tar.gz -C /
```

## Troubleshooting

### View Resources

```bash
# All resources in namespace
kubectl get all -n rag-ai-agent

# Specific resource types
kubectl get pods,svc,deploy -n rag-ai-agent
```

### Describe Resources

```bash
kubectl describe pod <pod-name> -n rag-ai-agent
kubectl describe svc backend-service -n rag-ai-agent
```

### View Logs

```bash
# Current logs
kubectl logs -n rag-ai-agent deployment/backend

# Follow logs
kubectl logs -n rag-ai-agent deployment/backend -f

# Previous container logs
kubectl logs -n rag-ai-agent <pod-name> --previous
```

### Execute Commands in Pod

```bash
kubectl exec -it -n rag-ai-agent <pod-name> -- /bin/bash
```

### Check Events

```bash
kubectl get events -n rag-ai-agent --sort-by='.lastTimestamp'
```

## Updates and Rollbacks

### Update Deployment

```bash
# Update image
kubectl set image deployment/backend backend=rag-ai-agent-backend:v2 -n rag-ai-agent

# Or apply updated manifest
kubectl apply -f k8s/backend-deployment.yaml
```

### Rollback

```bash
# View rollout history
kubectl rollout history deployment/backend -n rag-ai-agent

# Rollback to previous version
kubectl rollout undo deployment/backend -n rag-ai-agent

# Rollback to specific revision
kubectl rollout undo deployment/backend --to-revision=2 -n rag-ai-agent
```

### Check Rollout Status

```bash
kubectl rollout status deployment/backend -n rag-ai-agent
```

## Cleanup

### Remove All Resources

```bash
# Using script
./scripts/cleanup-k8s.sh

# Or manually
kubectl delete namespace rag-ai-agent
```

### Remove Specific Resources

```bash
kubectl delete -f k8s/ingress.yaml
kubectl delete deployment backend -n rag-ai-agent
```

## Best Practices

1. **Use namespaces** - Keep resources isolated
2. **Set resource limits** - Prevent resource exhaustion
3. **Configure health checks** - Enable automatic recovery
4. **Use persistent storage** - Don't lose data on pod restarts
5. **Implement backups** - Regular PVC backups
6. **Monitor resources** - Track CPU, memory, disk usage
7. **Use ConfigMaps/Secrets** - Externalize configuration
8. **Version control** - Keep manifests in git (except secrets)
9. **Test changes** - Use staging environment
10. **Document customizations** - Update this README with changes
