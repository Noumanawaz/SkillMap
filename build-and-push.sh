#!/bin/bash
# Script to build and push Docker images to Docker Hub

DOCKER_USERNAME="nomi2k4"

# Ensure buildx is available and create builder if needed
echo "🔧 Setting up Docker buildx..."
docker buildx create --use --name multiarch-builder 2>/dev/null || docker buildx use multiarch-builder
BACKEND_IMAGE="skillmap-backend"
FRONTEND_IMAGE="skillmap-frontend"
VERSION=${1:-latest}

echo "🐳 Building and pushing Docker images..."
echo "Docker Hub Username: $DOCKER_USERNAME"
echo "Version: $VERSION"
echo ""

# Build and push backend
echo "📦 Building backend image for linux/amd64..."
cd skillmap-ai/backend
docker buildx build --platform linux/amd64 -t $DOCKER_USERNAME/$BACKEND_IMAGE:$VERSION -t $DOCKER_USERNAME/$BACKEND_IMAGE:latest --push .
if [ $? -ne 0 ]; then
    echo "❌ Backend build failed"
    exit 1
fi

# Image is already pushed via buildx --push flag
cd ../..

# Build and push frontend
echo "📦 Building frontend image for linux/amd64..."
cd skillmap-ai/frontend
docker buildx build --platform linux/amd64 -t $DOCKER_USERNAME/$FRONTEND_IMAGE:$VERSION -t $DOCKER_USERNAME/$FRONTEND_IMAGE:latest --build-arg VITE_API_URL= --push .
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed"
    exit 1
fi

# Image is already pushed via buildx --push flag
cd ../..

echo ""
echo "✅ Successfully built and pushed all images!"
echo "Backend: $DOCKER_USERNAME/$BACKEND_IMAGE:latest"
echo "Frontend: $DOCKER_USERNAME/$FRONTEND_IMAGE:latest"
echo ""
echo "Next steps:"
echo "1. Update docker-compose.yml to use these images"
echo "2. Deploy to Coolify using 'Docker Compose Empty' option"

