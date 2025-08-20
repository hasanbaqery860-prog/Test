# Setting Up SSL Certificates for Zitadel

## Option 1: Self-Signed Certificates (Development/Testing)

```bash
# Create self-signed certificates
cd ~/zitadel-setup/certs

# Generate private key
openssl genrsa -out privkey.pem 2048

# Generate self-signed certificate
openssl req -new -x509 -key privkey.pem -out fullchain.pem -days 365 \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=auth.yourdomain.com"

# Verify files exist
ls -la
# Should show: privkey.pem and fullchain.pem
```

## Option 2: Let's Encrypt (Production - Recommended)

### Using Certbot Standalone:
```bash
# Install certbot
sudo apt update
sudo apt install certbot

# Get certificate (replace with your domain)
sudo certbot certonly --standalone -d auth.yourdomain.com

# Copy certificates to your zitadel directory
sudo cp /etc/letsencrypt/live/auth.yourdomain.com/privkey.pem ~/zitadel-setup/certs/
sudo cp /etc/letsencrypt/live/auth.yourdomain.com/fullchain.pem ~/zitadel-setup/certs/
sudo chown $USER:$USER ~/zitadel-setup/certs/*
```

### Using Certbot with DNS Challenge:
```bash
# For domains not yet pointing to this server
sudo certbot certonly --manual --preferred-challenges dns -d auth.yourdomain.com
```

## Option 3: Run Without SSL (Development Only)

Update your docker-compose.yml to remove nginx and expose Zitadel directly:

```yaml
version: '3.8'

services:
  zitadel:
    image: ghcr.io/zitadel/zitadel:v2.42.0
    command: ["start-from-init", "--masterkeyFromEnv", "--tlsMode", "disabled"]
    environment:
      - ZITADEL_EXTERNALPORT=8080
      - ZITADEL_EXTERNALDOMAIN=localhost  # Change to localhost
      - ZITADEL_EXTERNALSECURE=false      # Set to false
      - ZITADEL_TLS_ENABLED=false
      - ZITADEL_MASTERKEY=${ZITADEL_MASTERKEY}
      - ZITADEL_DATABASE_POSTGRES_HOST=postgres
      - ZITADEL_DATABASE_POSTGRES_PORT=5432
      - ZITADEL_DATABASE_POSTGRES_DATABASE=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_USERNAME=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_PASSWORD=${POSTGRES_PASSWORD}
      - ZITADEL_DATABASE_POSTGRES_USER_SSL_MODE=disable
      - ZITADEL_DATABASE_POSTGRES_ADMIN_USERNAME=postgres
      - ZITADEL_DATABASE_POSTGRES_ADMIN_PASSWORD=${POSTGRES_PASSWORD}
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
      - zitadel-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=zitadel
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - zitadel-network

  # nginx service removed for now

volumes:
  postgres-data:

networks:
  zitadel-network:
    driver: bridge
```

## Option 4: Use Existing Certificates

If you have certificates from another source:
```bash
# Copy your certificates
cp /path/to/your/certificate.crt ~/zitadel-setup/certs/fullchain.pem
cp /path/to/your/private.key ~/zitadel-setup/certs/privkey.pem

# Set proper permissions
chmod 644 ~/zitadel-setup/certs/fullchain.pem
chmod 600 ~/zitadel-setup/certs/privkey.pem
```

## Quick Start Without SSL (Recommended for Testing)

1. Create a simplified docker-compose.yml:

```bash
cat > docker-compose-no-ssl.yml << 'EOF'
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
      - ZITADEL_MASTERKEY=ThisIsATestMasterKey32Characters
      - ZITADEL_DATABASE_POSTGRES_HOST=postgres
      - ZITADEL_DATABASE_POSTGRES_PORT=5432
      - ZITADEL_DATABASE_POSTGRES_DATABASE=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_USERNAME=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_PASSWORD=zitadelpass
      - ZITADEL_DATABASE_POSTGRES_USER_SSL_MODE=disable
      - ZITADEL_DATABASE_POSTGRES_ADMIN_USERNAME=postgres
      - ZITADEL_DATABASE_POSTGRES_ADMIN_PASSWORD=postgrespass
      - ZITADEL_DATABASE_POSTGRES_ADMIN_SSL_MODE=disable
      - ZITADEL_FIRSTINSTANCE_ORG_NAME=TestOrg
      - ZITADEL_FIRSTINSTANCE_ORG_HUMAN_USERNAME=admin@example.com
      - ZITADEL_FIRSTINSTANCE_ORG_HUMAN_PASSWORD=Password1!
    ports:
      - '8080:8080'
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=zitadel
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgrespass
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
EOF
```

2. Run it:
```bash
docker-compose -f docker-compose-no-ssl.yml up -d
```

3. Access Zitadel at: http://localhost:8080

This will get you running immediately without SSL certificates!