# Zitadel Self-Hosted with Open edX Integration Guide (Simple Version)

This guide shows how to integrate Zitadel with Open edX using the built-in OIDC support. No SSL/nginx required for development.

## Prerequisites

- Docker and Docker Compose installed
- Open edX instance with Tutor

## Step 1: Setup Zitadel

### Create Directory and Files

```bash
mkdir zitadel-setup && cd zitadel-setup
```

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  zitadel:
    image: ghcr.io/zitadel/zitadel:v2.42.0
    command: ["start-from-init", "--masterkeyFromEnv", "--tlsMode", "disabled"]
    environment:
      - ZITADEL_EXTERNALPORT=8080
      - ZITADEL_EXTERNALDOMAIN=localhost  # Use localhost for local development
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
      - ZITADEL_FIRSTINSTANCE_ORG_NAME=MyOrganization
      - ZITADEL_FIRSTINSTANCE_ORG_HUMAN_USERNAME=admin@example.com
      - ZITADEL_FIRSTINSTANCE_ORG_HUMAN_PASSWORD=Admin123!
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
      - POSTGRES_PASSWORD=postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  postgres-data:
```

### Start Zitadel

```bash
# NOTE: For IP-based access, use 'localhost' in ZITADEL_EXTERNALDOMAIN
# Then access via http://YOUR_SERVER_IP:8080

# IMPORTANT: If you get password errors, clean up old data first:
docker compose down -v
docker volume rm zitadel-setup_postgres-data 2>/dev/null || true

# Start fresh
docker compose up -d

# Check logs
docker compose logs -f zitadel
```

Wait until you see: `server is listening on [::]:8080`

## Step 2: Configure Zitadel

1. Access Zitadel at `http://YOUR_SERVER_IP:8080` (where YOUR_SERVER_IP is your actual server IP)
2. Login: `admin@example.com` / `Admin123!`
3. Create a new Project: **"Open edX"**
4. Create a new Application:
   - Name: **Open edX**
   - Type: **Web Application**
   - Authentication Method: **OIDC**
5. Configure OIDC settings:
   - Grant Types: **Authorization Code, Refresh Token**
   - Redirect URIs: `http://YOUR_OPENEDX_DOMAIN/auth/complete/oidc/`
   - Post Logout URI: `http://YOUR_OPENEDX_DOMAIN/logout`
6. Save and note the **Client ID** and **Client Secret**

## Step 3: Configure Open edX with Tutor

### Create Tutor Plugin

Create file `$(tutor config printroot)/plugins/zitadel_oauth2.py`:

```python
from tutor import hooks

# Update these values
ZITADEL_DOMAIN = "http://YOUR_SERVER_IP:8080"  # Your Zitadel URL
ZITADEL_CLIENT_ID = "YOUR_CLIENT_ID"          # From Zitadel
ZITADEL_CLIENT_SECRET = "YOUR_CLIENT_SECRET"  # From Zitadel

# LMS Configuration
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        f"""
# Enable third party authentication
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
FEATURES["ENABLE_COMBINED_LOGIN_REGISTRATION"] = True
FEATURES["ALLOW_PUBLIC_ACCOUNT_CREATION"] = True

# Use built-in OIDC backend
THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# Zitadel configuration
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = "{ZITADEL_DOMAIN}"
SOCIAL_AUTH_OIDC_KEY = "{ZITADEL_CLIENT_ID}"
SOCIAL_AUTH_OIDC_SECRET = "{ZITADEL_CLIENT_SECRET}"

# Add to authentication backends
AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

# Allow auto account creation
SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False
SKIP_EMAIL_VERIFICATION = True

# CORS for Zitadel
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "{ZITADEL_DOMAIN}",
]
"""
    )
)

# CMS Configuration
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-cms-common-settings",
        f"""
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = "{ZITADEL_DOMAIN}"
SOCIAL_AUTH_OIDC_KEY = "{ZITADEL_CLIENT_ID}"
SOCIAL_AUTH_OIDC_SECRET = "{ZITADEL_CLIENT_SECRET}"

AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False
"""
    )
)
```

### Enable the Plugin

```bash
tutor plugins enable zitadel_oauth2
tutor config save
tutor images build openedx
tutor local restart
```

## Step 4: Configure Provider in Django Admin

1. Access: `http://YOUR_OPENEDX_DOMAIN/admin`
2. Navigate to **Third Party Auth** → **OAuth2 Provider Config**
3. Add new provider:
   - **Name**: oidc
   - **Slug**: oidc
   - **Backend name**: `social_core.backends.open_id_connect.OpenIdConnectAuth`
   - **Client ID**: (from Zitadel)
   - **Client Secret**: (from Zitadel)
   - **Skip registration form**: ✓
   - **Skip email verification**: ✓
   - **Enabled**: ✓

## Testing

1. Navigate to `http://YOUR_OPENEDX_DOMAIN/login`
2. Click "Sign in with oidc"
3. Login with Zitadel credentials
4. You'll be redirected back to Open edX

Direct OAuth URL:
```
http://YOUR_OPENEDX_DOMAIN/auth/login/oidc/?next=/dashboard
```

## Troubleshooting

**Domain Invalid Character Error**: Zitadel requires a valid domain format. Use `localhost` in ZITADEL_EXTERNALDOMAIN, not an IP address. You can still access it via `http://YOUR_IP:8080`.

**PostgreSQL password authentication failed**: This happens when there's old data from a previous run. Fix it by:
```bash
docker compose down -v
docker volume rm zitadel-setup_postgres-data
docker compose up -d
```

**Connection refused**: Make sure to use the correct IP address that's accessible from your Open edX instance

**OAuth Error**: Verify redirect URIs match exactly

**No Login Button**: Check provider is enabled in Django Admin

**Version warning**: The `version` attribute warning can be ignored, or remove the first line from docker-compose.yml

That's it! Zitadel is now integrated with Open edX.