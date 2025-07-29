#!/bin/bash

# CoinFolio Analytics Deployment Script
# This script helps deploy your application with proper database persistence

set -e  # Exit on any error

echo "🚀 CoinFolio Analytics Deployment Script"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data
mkdir -p backups
mkdir -p logs

# Set proper permissions
chmod 755 data backups logs

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Please edit .env file and change the secret keys!"
    echo "   You can generate secure keys with: python3 -c 'import secrets; print(secrets.token_hex(32))'"
fi

# Function to generate secure key
generate_key() {
    python3 -c "import secrets; print(secrets.token_hex(32))"
}

# Ask user if they want to generate new keys
read -p "🔑 Do you want to generate new secure keys? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    SECRET_KEY=$(generate_key)
    JWT_SECRET_KEY=$(generate_key)
    
    # Update .env file
    sed -i.bak "s/SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i.bak "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/" .env
    
    echo "✅ New keys generated and saved to .env file"
fi

# Build and start the application
echo "🔨 Building and starting the application..."
docker-compose up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if API is healthy
if curl -f http://localhost:5001/api/health &> /dev/null; then
    echo "✅ API is healthy and running on http://localhost:5001"
else
    echo "❌ API health check failed"
    echo "📊 Checking logs..."
    docker-compose logs api
    exit 1
fi

# Check if frontend is accessible
if curl -f http://localhost:3000 &> /dev/null; then
    echo "✅ Frontend is running on http://localhost:3000"
else
    echo "⚠️  Frontend might still be starting up..."
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Services Status:"
docker-compose ps

echo ""
echo "🔗 Access your application:"
echo "   Frontend: http://localhost:3000"
echo "   API:      http://localhost:5001"
echo ""
echo "📋 Useful commands:"
echo "   View logs:        docker-compose logs"
echo "   Stop services:    docker-compose down"
echo "   Restart:          docker-compose restart"
echo "   Update:           docker-compose pull && docker-compose up -d"
echo ""
echo "💾 Database Management:"
echo "   Backup:           python3 database_backup.py backup"
echo "   List backups:     python3 database_backup.py list"
echo "   Restore:          python3 database_backup.py restore --backup-file <file>"
echo ""
echo "⚠️  Remember to:"
echo "   1. Set up regular database backups"
echo "   2. Configure SSL/HTTPS for production"
echo "   3. Set up monitoring and logging"
echo "   4. Update passwords and secrets" 