#!/bin/bash

# RestoVoice AI Backend Docker Quick Start Script

set -e

echo "🚀 Starting RestoVoice AI Backend with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your actual API keys before running the services."
    echo "   Required variables:"
    echo "   - VAPI_API_KEY"
    echo "   - AZURE_OPENAI_API_KEY"
    echo "   - ELEVENLABS_API_KEY"
    echo ""
    read -p "Press Enter to continue after configuring .env file..."
fi

# Choose environment
echo "🌍 Choose environment:"
echo "1) Development (with live reload)"
echo "2) Production (optimized)"
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        COMPOSE_FILE="docker-compose.dev.yml"
        echo "🔧 Starting development environment..."
        ;;
    2)
        COMPOSE_FILE="docker-compose.prod.yml"
        echo "🚀 Starting production environment..."
        ;;
    *)
        echo "❌ Invalid choice. Defaulting to development."
        COMPOSE_FILE="docker-compose.dev.yml"
        ;;
esac

# Build and start services
echo "🏗️  Building Docker images..."
docker-compose -f $COMPOSE_FILE build

echo "🚀 Starting services..."
docker-compose -f $COMPOSE_FILE up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ AI Backend is healthy"
else
    echo "⚠️  AI Backend might still be starting..."
fi

# Check database health
if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL is healthy"
else
    echo "⚠️  PostgreSQL might still be starting..."
fi

echo ""
echo "🎉 RestoVoice AI Backend is starting up!"
echo ""
echo "📍 Available endpoints:"
echo "   - API: http://localhost:8000"
echo "   - Health: http://localhost:8000/health"
echo "   - Documentation: http://localhost:8000/docs"
echo "   - Database: localhost:5439"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "   - Stop services: docker-compose -f $COMPOSE_FILE down"
echo "   - Restart services: docker-compose -f $COMPOSE_FILE restart"
echo ""
echo "🔧 To test the integration:"
echo "   curl http://localhost:8000/v1/vapi/voices/elevenlabs"
echo ""
echo "📖 For more information, see DOCKER_SETUP.md"
