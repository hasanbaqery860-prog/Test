# Working Zitadel + Open edX Setup (No SMS)

## Step 1: Simple Docker Compose

Create `docker-compose.yml`:

```yaml
services:
  zitadel:
    image: ghcr.io/zitadel/zitadel:v2.42.0
    command: ["start-from-init", "--masterkeyFromEnv", "--tlsMode", "disabled"]
    environment:
      - ZITADEL_EXTERNALPORT=8090
      - ZITADEL_EXTERNALDOMAIN=localhost
      - ZITADEL_EXTERNALSECURE=false
      - ZITADEL_MASTERKEY=GVLVFDTSIFXndQLNMd3H6yvwP3cTlnHC
      - ZITADEL_DATABASE_POSTGRES_HOST=postgres
      - ZITADEL_DATABASE_POSTGRES_PORT=5432
      - ZITADEL_DATABASE_POSTGRES_DATABASE=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_USERNAME=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_PASSWORD=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_SSL_MODE=disable
      - ZITADEL_DATABASE_POSTGRES_ADMIN_USERNAME=postgres
      - ZITADEL_DATABASE_POSTGRES_ADMIN_PASSWORD=postgres
      - ZITADEL_DATABASE_POSTGRES_ADMIN_SSL_MODE=disable
    ports:
      - '8090:8080'
    depends_on:
      postgres:
        condition: service_healthy

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=zitadel
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      retries: 5
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

## Step 2: Start It

```bash
# Clean start
docker compose down -v
docker volume rm zitadel-setup_postgres-data 2>/dev/null || true

# Start
docker compose up -d

# Wait and check
sleep 30
docker compose logs zitadel
```

## Step 3: Access and Configure

1. Go to: `http://YOUR-IP:8090`
2. First time setup will create admin user
3. Create Project → Create App → Get Client ID/Secret

## Step 4: Basic Open edX Integration

Just add these to your Open edX settings:

```python
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = "http://YOUR-IP:8090"
SOCIAL_AUTH_OIDC_KEY = "your-client-id"
SOCIAL_AUTH_OIDC_SECRET = "your-client-secret"
```

That's it! Basic OAuth working.

---

# If You REALLY Need SMS/Phone Login

The issue is that Zitadel's SMS feature requires:
1. Proper SMS provider configuration (complex)
2. Passwordless setup (not well documented)
3. Phone number verification flow

Honestly, for Open edX, you probably just need OAuth login (username/password through Zitadel).

If you MUST have phone+OTP, consider:
- Using a different solution (Supertokens, Auth0)
- Building a custom middleware
- Using Zitadel API directly to implement phone auth