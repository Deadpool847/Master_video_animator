#!/bin/bash

# Video Art Masterpiece - Docker Setup Script
echo "🐳 Video Art Masterpiece - Docker Setup"
echo "========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found! Please install Docker first."
    echo "📥 Download from: https://www.docker.com/get-started"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose not found! Please update Docker."
    exit 1
fi

echo "✅ Docker found:"
docker --version
echo ""

echo "🧹 Cleaning up any existing containers..."
docker compose down -v 2>/dev/null

echo "📦 Building and starting Video Art Masterpiece..."
echo "This may take 5-10 minutes for first-time setup..."
echo ""

if ! docker compose up --build -d; then
    echo "❌ Failed to start containers!"
    echo ""
    echo "Checking container status..."
    docker compose ps
    echo ""
    echo "Checking logs..."
    docker compose logs --tail=20
    exit 1
fi

echo ""
echo "🎉 Video Art Masterpiece is starting up!"
echo ""
echo "📊 Container status:"
docker compose ps

echo ""
echo "🌐 Application URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001"
echo "  Database: mongodb://localhost:27017"
echo ""

echo "⏳ Waiting for services to be ready..."
sleep 10

echo "🔍 Health check:"
if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️ Backend not ready yet, please wait a moment..."
fi

if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ Frontend is healthy!"
else
    echo "⚠️ Frontend not ready yet, please wait a moment..."
fi

echo ""
echo "🎨 Ready to create video masterpieces!"
echo "Open http://localhost:3000 in your browser"
echo ""

echo "📋 Useful Docker commands:"
echo "  View logs: docker compose logs -f"
echo "  Stop: docker compose down"
echo "  Restart: docker compose restart"
echo "  Status: docker compose ps"
echo ""