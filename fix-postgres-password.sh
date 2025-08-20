#!/bin/bash

echo "=== Fixing PostgreSQL Password Issue ==="
echo

# Option 1: Complete Reset (Recommended)
echo "Option 1: Complete Reset (Recommended)"
echo "This will delete all data and start fresh"
echo
echo "Run these commands:"
echo
cat << 'EOF'
# 1. Stop all containers
docker compose down

# 2. Remove the postgres volume (this will delete all data!)
docker volume rm zitadel-setup_postgres-data

# 3. Create a new .env file with fresh passwords
cat > .env << 'EOL'
ZITADEL_MASTERKEY=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
EOL

# 4. Start fresh
docker compose up -d
EOF

echo
echo "----------------------------------------"
echo

# Option 2: Use the existing password
echo "Option 2: Find and use the existing password"
echo
echo "If you remember the original password, update your .env file:"
echo "POSTGRES_PASSWORD=your-original-password"
echo

echo "----------------------------------------"
echo

# Option 3: Quick development setup without .env
echo "Option 3: Quick development setup (no .env needed)"
echo
cat << 'EOF'
# Create a simple docker-compose file with hardcoded passwords
cat > docker-compose-dev.yml << 'DEVEOF'
version: '3.8'

services:
  zitadel:
    image: ghcr.io/zitadel/zitadel:v2.42.0
    command: ["start-from-init", "--masterkeyFromEnv", "--tlsMode", "disabled"]
    environment:
      - ZITADEL_EXTERNALPORT=8080
      - ZITADEL_EXTERNALDOMAIN=localhost:8080
      - ZITADEL_EXTERNALSECURE=false
      - ZITADEL_TLS_ENABLED=false
      - ZITADEL_MASTERKEY=GVLVFDTSIFXndQLNMd3H6yvwP3cTlnHCGvLVFDTSIFXndQLNMd3H6yvwP3cTlnHC
      - ZITADEL_DATABASE_POSTGRES_HOST=postgres
      - ZITADEL_DATABASE_POSTGRES_PORT=5432
      - ZITADEL_DATABASE_POSTGRES_DATABASE=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_USERNAME=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_PASSWORD=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_SSL_MODE=disable
      - ZITADEL_DATABASE_POSTGRES_ADMIN_USERNAME=postgres
      - ZITADEL_DATABASE_POSTGRES_ADMIN_PASSWORD=postgres
      - ZITADEL_DATABASE_POSTGRES_ADMIN_SSL_MODE=disable
      - ZITADEL_FIRSTINSTANCE_ORG_NAME=MyOrg
      - ZITADEL_FIRSTINSTANCE_ORG_HUMAN_USERNAME=admin@example.com
      - ZITADEL_FIRSTINSTANCE_ORG_HUMAN_PASSWORD=Password1!
    ports:
      - '8080:8080'
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - zitadel

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=zitadel
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - postgres-dev-data:/var/lib/postgresql/data
    networks:
      - zitadel

volumes:
  postgres-dev-data:

networks:
  zitadel:
DEVEOF

# Run it
docker compose -f docker-compose-dev.yml down -v
docker compose -f docker-compose-dev.yml up -d
EOF

echo
echo "Choose one of the options above to fix the password issue."