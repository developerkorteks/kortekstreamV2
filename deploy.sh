#!/bin/bash

echo "🚀 Starting deployment..."

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker compose -f docker-compose.prod.yml down

# Build and start services
echo "🔨 Building and starting services..."
docker compose -f docker-compose.prod.yml up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check health
echo "🔍 Checking service health..."
docker compose -f docker-compose.prod.yml ps

# Test application
echo "🧪 Testing application..."
if curl -f http://localhost:9111/health/ > /dev/null 2>&1; then
    echo "✅ Application is healthy and ready!"
    echo "🌐 Access your application at: http://localhost:9111"
else
    echo "❌ Application health check failed"
    echo "📋 Checking logs..."
    docker compose -f docker-compose.prod.yml logs --tail=20 web
fi

echo "🏁 Deployment completed!"