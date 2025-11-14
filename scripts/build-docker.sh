#!/bin/bash

# Build Docker images for OpenChat

set -e

echo "🐳 Building Docker images..."

# Build backend image
echo "Building backend image..."
docker build -t openchat-backend:latest -f backend/Dockerfile backend/

# Build frontend image
echo "Building frontend image..."
docker build -t openchat-frontend:latest -f frontend/Dockerfile frontend/

echo "✅ Docker images built successfully"
echo ""
echo "Images:"
echo "  - openchat-backend:latest"
echo "  - openchat-frontend:latest"
