#!/bin/bash

# Quick start script for Zitadel with Open edX integration

echo "Starting Zitadel setup..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    
    # Generate secure keys
    MASTER_KEY=$(openssl rand -base64 32)
    POSTGRES_PASS=$(openssl rand -base64 32)
    WEBHOOK_SECRET=$(openssl rand -base64 32)
    
    # Update .env with generated values
    sed -i "s/your-generated-master-key-here/$MASTER_KEY/g" .env
    sed -i "s/your-secure-postgres-password/$POSTGRES_PASS/g" .env
    sed -i "s/your-webhook-secret/$WEBHOOK_SECRET/g" .env
    
    echo "Generated secure keys in .env file"
    echo "Please update the following in .env:"
    echo "  - KAVENEGAR_API_KEY"
    echo "  - SMTP settings (if needed)"
    echo "  - Domain names"
fi

# Create SSL certificate directory
mkdir -p certs
echo "Please place your SSL certificates in the certs/ directory:"
echo "  - certs/fullchain.pem"
echo "  - certs/privkey.pem"

# Build and start services
echo "Building services..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Zitadel is starting up..."
echo "Access the admin console at: https://auth.yourdomain.com"
echo "Default admin credentials are in config/instance-config.yaml"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"