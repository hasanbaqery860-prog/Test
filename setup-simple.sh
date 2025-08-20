#!/bin/bash

# Simple setup script for Zitadel with Open edX integration

echo "=== Zitadel + Open edX Setup Script ==="
echo

# Check if running in correct directory
if [ ! -f "docker-compose-simple.yml" ]; then
    echo "Error: Please run this script from the zitadel-setup directory"
    exit 1
fi

# Create necessary directories
echo "Creating directories..."
mkdir -p config certs

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Zitadel Configuration
ZITADEL_MASTERKEY=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
EOF
    echo "✓ Generated secure keys in .env"
else
    echo "✓ Using existing .env file"
fi

# Check if instance config exists
if [ ! -f config/instance-config.yaml ]; then
    echo "Creating instance configuration..."
    read -p "Enter admin email: " ADMIN_EMAIL
    read -p "Enter organization name: " ORG_NAME
    
    cat > config/instance-config.yaml << EOF
FirstInstance:
  Org:
    Name: '${ORG_NAME}'
    Human:
      UserName: '${ADMIN_EMAIL}'
      FirstName: 'Admin'
      LastName: 'User'
      Email:
        Address: '${ADMIN_EMAIL}'
        Verified: true
      Password: 'ChangeMeImmediately123!'
EOF
    echo "✓ Created instance configuration"
fi

# Check SSL certificates
if [ ! -f certs/fullchain.pem ] || [ ! -f certs/privkey.pem ]; then
    echo
    echo "⚠️  SSL certificates not found!"
    echo "Please place your SSL certificates in:"
    echo "  - certs/fullchain.pem"
    echo "  - certs/privkey.pem"
    echo
    read -p "Press Enter to continue without SSL (development only)..."
fi

# Start services
echo
echo "Starting Zitadel services..."
docker-compose -f docker-compose-simple.yml up -d

echo
echo "✓ Zitadel is starting up!"
echo
echo "=== Next Steps ==="
echo "1. Wait ~30 seconds for initialization"
echo "2. Access Zitadel at: http://localhost:8080 (or https://auth.yourdomain.com)"
echo "3. Login with admin credentials (check config/instance-config.yaml)"
echo "4. Create OAuth application for Open edX"
echo "5. Copy the Tutor plugin to your Tutor plugins directory"
echo "6. Update plugin with your Client ID and Secret"
echo
echo "To view logs: docker-compose -f docker-compose-simple.yml logs -f"
echo "To stop: docker-compose -f docker-compose-simple.yml down"