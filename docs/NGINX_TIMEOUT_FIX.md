# Nginx 504 Gateway Timeout Fix

## Problem Description

Users were experiencing 504 Gateway Timeout errors when accessing the application through the nginx proxy. The error logs showed:

```
2026/02/15 11:18:23 [error] 30#30: *697 upstream timed out (110: Operation timed out) while connecting to upstream, client: 10.244.166.192, server: _, request: "GET / HTTP/1.1", upstream: "http://10.103.22.47:80/", host: "192.168.1.20:8083"
10.244.166.192 - - [15/Feb/2026:11:18:23 +0000] "GET / HTTP/1.1" 504 569
```

## Root Cause

The issue was caused by several configuration problems in the nginx proxy:

1. **No Connection Pooling**: Each request created a new TCP connection to upstream services, causing delays
2. **HTTP/1.0 Default**: Nginx was using HTTP/1.0 which doesn't support persistent connections
3. **No Failover Strategy**: When an upstream timed out, nginx didn't have proper retry logic

## Solution

The fix involved updating the nginx configuration in `k8s/nginx-proxy.yaml` with the following improvements:

### 1. Keepalive Connection Pools

Added connection pooling to maintain persistent connections to upstream services:

```nginx
upstream frontend {
    server frontend-service:80;
    keepalive 32;  # Maintain 32 idle keepalive connections
}

upstream backend {
    server backend-service:8000;
    keepalive 32;
}
```

### 2. HTTP/1.1 with Keepalive

Enabled HTTP/1.1 for all proxy locations to support persistent connections:

```nginx
proxy_http_version 1.1;
proxy_set_header Connection "";  # Clear Connection header for keepalive
```

### 3. Automatic Failover

Added retry logic for transient errors:

```nginx
proxy_next_upstream error timeout invalid_header http_500 http_502 http_503 http_504;
proxy_next_upstream_timeout 10s;
```

## Deployment

To apply the fix to your Kubernetes cluster:

```bash
# Apply the updated configuration
kubectl apply -f k8s/nginx-proxy.yaml

# Restart the nginx proxy to load new config
kubectl rollout restart deployment/nginx-proxy -n rag-ai-agent

# Watch the rollout status
kubectl rollout status deployment/nginx-proxy -n rag-ai-agent
```

## Verification

### 1. Check Pod Status

Ensure the nginx proxy pods are running:

```bash
kubectl get pods -n rag-ai-agent -l app=nginx-proxy
```

Expected output:
```
NAME                           READY   STATUS    RESTARTS   AGE
nginx-proxy-xxxxxxxxxx-xxxxx   1/1     Running   0          2m
```

### 2. Check Nginx Configuration

Verify the configuration was loaded correctly:

```bash
kubectl exec -n rag-ai-agent deployment/nginx-proxy -- nginx -t
```

Expected output:
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 3. Test Health Endpoint

Test the nginx health endpoint:

```bash
kubectl port-forward -n rag-ai-agent svc/nginx-proxy-service 8080:80
curl http://localhost:8080/nginx-health
```

Expected output:
```
healthy
```

### 4. Monitor Logs

Watch nginx logs for any timeout errors:

```bash
kubectl logs -n rag-ai-agent deployment/nginx-proxy -f
```

You should no longer see "upstream timed out" errors.

### 5. Test Application Access

Access the application through the nginx proxy:

```bash
# If using external IP
curl -I http://192.168.1.20:8083/

# If using port-forward
kubectl port-forward -n rag-ai-agent svc/nginx-proxy-service 8080:80
curl -I http://localhost:8080/
```

Expected: HTTP 200 or 304 response (not 504)

## Performance Benefits

The keepalive configuration provides several benefits:

1. **Reduced Latency**: Reusing connections eliminates TCP handshake overhead (typically 1-2 RTT)
2. **Lower Resource Usage**: Fewer connections means less memory and CPU usage
3. **Better Throughput**: Connection pooling allows for more efficient request handling
4. **Improved Reliability**: Automatic retries handle transient network issues

## Monitoring

To monitor the effectiveness of the fix:

### Connection Statistics

Check nginx connection statistics:

```bash
kubectl exec -n rag-ai-agent deployment/nginx-proxy -- nginx -V
```

### Response Times

Monitor response times through your application:

```bash
# Example using curl
time curl http://192.168.1.20:8083/
```

Response times should be consistently lower without timeout spikes.

### Error Rates

Check for 504 errors in nginx access logs:

```bash
kubectl logs -n rag-ai-agent deployment/nginx-proxy | grep " 504 "
```

After the fix, 504 errors should be eliminated or significantly reduced.

## Troubleshooting

If you still experience timeouts after applying the fix:

### 1. Check Backend Health

Verify backend services are healthy:

```bash
kubectl get pods -n rag-ai-agent -l app=backend
kubectl logs -n rag-ai-agent deployment/backend
```

### 2. Check Frontend Health

Verify frontend services are healthy:

```bash
kubectl get pods -n rag-ai-agent -l app=frontend
kubectl logs -n rag-ai-agent deployment/frontend
```

### 3. Check Service Endpoints

Ensure services have active endpoints:

```bash
kubectl get endpoints -n rag-ai-agent frontend-service
kubectl get endpoints -n rag-ai-agent backend-service
```

### 4. Network Connectivity

Test connectivity between nginx and backend:

```bash
kubectl exec -n rag-ai-agent deployment/nginx-proxy -- wget -O- http://backend-service:8000/health
kubectl exec -n rag-ai-agent deployment/nginx-proxy -- wget -O- http://frontend-service:80/
```

### 5. Resource Limits

Check if pods are being throttled due to resource limits:

```bash
kubectl top pods -n rag-ai-agent
kubectl describe pod -n rag-ai-agent <pod-name>
```

## Additional Tuning

If you need to further tune the configuration:

### Increase Keepalive Connections

For high-traffic scenarios, increase the keepalive pool:

```nginx
upstream backend {
    server backend-service:8000;
    keepalive 64;  # Increase from 32 to 64
}
```

### Adjust Timeouts

For long-running requests, increase timeouts:

```nginx
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
proxy_read_timeout 300s;
```

### Enable Access Logs

For debugging, enable access logs:

```nginx
access_log /var/log/nginx/access.log;
```

## References

- [Nginx HTTP Upstream Module](http://nginx.org/en/docs/http/ngx_http_upstream_module.html)
- [Nginx Keepalive Connections](http://nginx.org/en/docs/http/ngx_http_upstream_module.html#keepalive)
- [Nginx Proxy Module](http://nginx.org/en/docs/http/ngx_http_proxy_module.html)
