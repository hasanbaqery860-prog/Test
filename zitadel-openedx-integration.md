# Zitadel Self-Hosted with Open edX Integration Guide

This guide shows how to integrate Zitadel (self-hosted identity provider) with Open edX using the built-in OIDC support.

## Prerequisites

- Docker and Docker Compose installed
- Open edX instance with Tutor
- Domain with SSL certificates

## Step 1: Setup Zitadel with Docker Compose

### Create Directory Structure

```bash
mkdir -p zitadel-setup/{config,certs}
cd zitadel-setup
```

### Create docker-compose.yml

```yaml
version: '3.8'

services:
  zitadel:
    image: ghcr.io/zitadel/zitadel:latest
    command: 'start-from-init --masterkeyFromEnv --tlsMode disabled'
    environment:
      - ZITADEL_EXTERNALPORT=8080
      - ZITADEL_EXTERNALDOMAIN=auth.yourdomain.com
      - ZITADEL_EXTERNALSECURE=true
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
      - ZITADEL_FIRSTINSTANCE_PATPATH=/app/config/instance-config.yaml
    ports:
      - '8080:8080'
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./config/instance-config.yaml:/app/config/instance-config.yaml:ro
      - zitadel-certs:/app/certs
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

  nginx:
    image: nginx:alpine
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - zitadel
    networks:
      - zitadel-network

volumes:
  postgres-data:
  zitadel-certs:

networks:
  zitadel-network:
    driver: bridge
```

### Create .env file

```bash
# Generate secure keys
ZITADEL_MASTERKEY=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

### Create config/instance-config.yaml

```yaml
FirstInstance:
  Org:
    Name: 'Your Organization'
    Human:
      UserName: 'admin@yourdomain.com'
      FirstName: 'Admin'
      LastName: 'User'
      Email:
        Address: 'admin@yourdomain.com'
        Verified: true
      Password: 'ChangeMeImmediately123!'
```

### Create nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    upstream zitadel {
        server zitadel:8080;
    }

    server {
        listen 80;
        server_name auth.yourdomain.com;
        
        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    server {
        listen 443 ssl http2;
        server_name auth.yourdomain.com;

        ssl_certificate /etc/nginx/certs/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location / {
            proxy_pass http://zitadel;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

### Start Zitadel

```bash
# Add SSL certificates to certs/ directory
# Then start services
docker-compose up -d
```

## Step 2: Configure Zitadel

1. Access Zitadel at `https://auth.yourdomain.com`
2. Login with admin credentials from `instance-config.yaml`
3. Create a new Project: **"Open edX"**
4. Create a new Application:
   - Name: **Open edX**
   - Type: **Web Application**
   - Authentication Method: **OIDC**
5. Configure OIDC settings:
   - Grant Types: **Authorization Code, Refresh Token**
   - Redirect URIs: `https://your-openedx-domain.com/auth/complete/oidc/`
   - Post Logout URI: `https://your-openedx-domain.com/logout`
6. Save and note the **Client ID** and **Client Secret**

## Step 3: Configure Open edX with Tutor

### Create Tutor Plugin

Create file `$(tutor config printroot)/plugins/zitadel_oauth2.py`:

```python
"""
Tutor plugin for Zitadel OAuth2/OIDC integration
Uses Open edX's built-in OIDC backend
"""
from tutor import hooks

# Update these values
ZITADEL_DOMAIN = "https://auth.yourdomain.com"
ZITADEL_CLIENT_ID = "YOUR_CLIENT_ID"
ZITADEL_CLIENT_SECRET = "YOUR_CLIENT_SECRET"

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

# MFE Configuration
hooks.Filters.CONFIG_OVERRIDES.add_item(
    (
        "mfe",
        {
            "ENABLE_THIRD_PARTY_AUTH": True,
            "THIRD_PARTY_AUTH_ONLY_HINT": "oidc"
        }
    )
)
```

### Enable the Plugin

```bash
tutor plugins enable zitadel_oauth2
tutor config save
tutor images build openedx mfe
tutor local restart
```

## Step 4: Configure Provider in Django Admin

1. Access Django Admin: `https://your-openedx-domain.com/admin`
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

1. Navigate to `https://your-openedx-domain.com/login`
2. You should see a "Sign in with Zitadel" option
3. Click it to authenticate via Zitadel
4. After successful authentication, you'll be redirected to Open edX

Direct OAuth URL for testing:
```
https://your-openedx-domain.com/auth/login/oidc/?next=/dashboard
```

## Troubleshooting

**OAuth Error**: Verify redirect URIs match exactly and client credentials are correct

**403 Forbidden**: Ensure `SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False`

**No Login Button**: Check provider is enabled in Django Admin

**CORS Issues**: Verify Zitadel domain is in `CORS_ORIGIN_WHITELIST`

## Security Notes

- Always use HTTPS in production
- Keep client secrets secure
- Regularly update all components
- Use strong admin passwords

That's it! Zitadel is now integrated with Open edX using the built-in OIDC support.