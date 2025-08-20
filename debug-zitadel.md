# Debugging Zitadel "serve" Command Error

## Step 1: Check your docker-compose.yml

Make sure your docker-compose.yml has the correct command. It should look exactly like this:

```yaml
services:
  zitadel:
    image: ghcr.io/zitadel/zitadel:v2.42.0
    command: 'start-from-init --masterkeyFromEnv --tlsMode disabled'
    # NOT 'serve' or 'zitadel serve'
```

## Step 2: Stop and Clean Everything

```bash
# Stop all containers
docker-compose down

# Remove the Zitadel container completely
docker rm -f $(docker ps -aq -f name=zitadel)

# Remove any cached images
docker rmi ghcr.io/zitadel/zitadel:latest
docker rmi ghcr.io/zitadel/zitadel:v2.42.0
```

## Step 3: Check for Override Files

Make sure you don't have any override files:
```bash
ls -la docker-compose*.yml
# Should only show docker-compose.yml
```

## Step 4: Create Fresh docker-compose.yml

Create a new file called `docker-compose.yml` with this exact content:

```yaml
version: '3.8'

services:
  zitadel:
    image: ghcr.io/zitadel/zitadel:v2.42.0
    command: 'start-from-init --masterkeyFromEnv --tlsMode disabled'
    environment:
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
      - zitadel

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
      - zitadel

volumes:
  postgres-data:

networks:
  zitadel:
```

## Step 5: Create .env file

```bash
ZITADEL_MASTERKEY=your-32-character-master-key-here
POSTGRES_PASSWORD=your-secure-postgres-password
```

## Step 6: Start Fresh

```bash
# Pull the image fresh
docker pull ghcr.io/zitadel/zitadel:v2.42.0

# Start services
docker-compose up -d postgres
# Wait 10 seconds for postgres to be ready
sleep 10
docker-compose up -d zitadel
```

## Step 7: Check Logs

```bash
# Check what command is actually being run
docker-compose logs zitadel | head -20

# Check if container is running
docker-compose ps
```

## Step 8: Debug the Actual Command

If still failing, check what command Docker is actually running:

```bash
docker inspect $(docker-compose ps -q zitadel) | grep -A 5 "Cmd"
```

This should show you exactly what command is being passed to the container.

## Alternative: Use Explicit Entrypoint

If the issue persists, try this alternative in docker-compose.yml:

```yaml
  zitadel:
    image: ghcr.io/zitadel/zitadel:v2.42.0
    entrypoint: ["/app/zitadel"]
    command: ['start-from-init', '--masterkeyFromEnv', '--tlsMode', 'disabled']
    # ... rest of configuration
```

## Common Issues

1. **Old cached image**: The 'latest' tag might have an old version cached
2. **Override in .env**: Check if COMPOSE_FILE or other env vars are set
3. **Wrong working directory**: Make sure you're in the correct directory
4. **Copy-paste issues**: Hidden characters or wrong quotes in the command

Let me know which step reveals the issue!