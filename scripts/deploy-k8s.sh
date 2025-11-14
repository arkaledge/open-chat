#!/bin/bash

# Deploy OpenChat to Kubernetes

set -e

echo "☸️  Deploying OpenChat to Kubernetes..."

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed. Please install kubectl first."
    exit 1
fi

# Create namespace
echo "Creating namespace..."
kubectl apply -f k8s/base/namespace.yaml

# Create secrets (you need to edit this with your actual secrets)
echo "⚠️  Creating secrets..."
echo "Please ensure you have updated the secret values!"

kubectl create secret generic openchat-secrets \
  --namespace=openchat \
  --from-literal=database-url="postgresql://openchat:changeme@postgres:5432/openchat" \
  --from-literal=redis-url="redis://redis:6379/0" \
  --from-literal=secret-key="$(openssl rand -hex 32)" \
  --from-literal=jwt-secret="$(openssl rand -hex 32)" \
  --from-literal=postgres-password="changeme" \
  --from-literal=openai-api-key="" \
  --from-literal=anthropic-api-key="" \
  --dry-run=client -o yaml | kubectl apply -f -

# Deploy PostgreSQL
echo "Deploying PostgreSQL..."
kubectl apply -f k8s/base/postgres-statefulset.yaml

# Deploy Redis, Qdrant, MinIO
echo "Deploying infrastructure services..."
kubectl apply -f k8s/base/redis-deployment.yaml || true
kubectl apply -f k8s/base/qdrant-deployment.yaml || true
kubectl apply -f k8s/base/minio-deployment.yaml || true

# Wait for database to be ready
echo "Waiting for database..."
kubectl wait --for=condition=ready pod -l app=postgres --namespace=openchat --timeout=300s

# Deploy backend
echo "Deploying backend..."
kubectl apply -f k8s/base/backend-deployment.yaml

# Deploy frontend
echo "Deploying frontend..."
kubectl apply -f k8s/base/frontend-deployment.yaml

# Deploy ingress
echo "Deploying ingress..."
kubectl apply -f k8s/base/ingress.yaml

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Check status:"
echo "  kubectl get pods -n openchat"
echo ""
echo "Access logs:"
echo "  kubectl logs -f deployment/openchat-backend -n openchat"
echo ""
