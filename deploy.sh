#!/bin/bash

# High-Performance IP and Browser Detection API Deployment Script

set -e

echo "🚀 Deploying IP and Browser Detection API..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $port is already in use. Please stop the service using that port."
        return 1
    fi
    return 0
}

# Check if ports are available
echo "🔍 Checking port availability..."
if ! check_port 8080; then
    exit 1
fi

if ! check_port 6379; then
    echo "⚠️  Port 6379 (Redis) is in use. The API will use the existing Redis instance."
fi

# Build and start the services
echo "📦 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if the API is responding
echo "🔍 Checking API health..."
max_attempts=30
attempt=1

while [ $attempt -le $max_attempts ]; do
    if curl -f http://localhost:8080/api/health > /dev/null 2>&1; then
        echo "✅ API is healthy and ready!"
        break
    else
        echo "⏳ Waiting for API to be ready... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    fi
done

if [ $attempt -gt $max_attempts ]; then
    echo "❌ API failed to start within the expected time."
    echo "📋 Checking logs..."
    docker-compose logs api
    exit 1
fi

# Display service information
echo ""
echo "🎉 Deployment successful!"
echo ""
echo "📋 Service Information:"
echo "   API URL: http://localhost:8080"
echo "   Health Check: http://localhost:8080/api/health"
echo "   Redis: localhost:6379"
echo ""
echo "🔑 API Keys:"
echo "   Web Frontend: web_1234567890abcdef"
echo "   Android App: android_9876543210fedcba"
echo "   Other Projects: other_abcdef1234567890"
echo ""
echo "📚 Quick Test:"
echo "   curl -H 'X-API-Key: web_1234567890abcdef' http://localhost:8080/api/detect/simple"
echo ""
echo "🛠️  Management Commands:"
echo "   View logs: docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart services: docker-compose restart"
echo "   Update and restart: docker-compose up -d --build"
echo ""

# Run a quick test
echo "🧪 Running quick test..."
if curl -s -H "X-API-Key: web_1234567890abcdef" http://localhost:8080/api/detect/simple > /dev/null; then
    echo "✅ API test successful!"
else
    echo "⚠️  API test failed. Check logs with: docker-compose logs api"
fi

echo ""
echo "🎯 Your high-performance IP and browser detection API is now running!"