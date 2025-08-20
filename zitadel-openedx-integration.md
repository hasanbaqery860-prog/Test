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
      - ZITADEL_EXTERNALPORT=8090
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
      - '8090:8080'  # Changed to 8090 to avoid conflicts
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
# Then access via http://YOUR_SERVER_IP:8090

# IMPORTANT: If you get password errors, clean up old data first:
docker compose down -v
docker volume rm zitadel-setup_postgres-data 2>/dev/null || true

# Start fresh
docker compose up -d

# Check logs
docker compose logs -f zitadel
```

Wait until you see: `server is listening on [::]:8080` (internal port)

## Step 2: Configure Zitadel

1. Access Zitadel at `http://YOUR_SERVER_IP:8090` (where YOUR_SERVER_IP is your actual server IP)
2. Login: `admin@example.com` / `Admin123!`
3. Create a new Project:
   - Click **Projects** in the left menu
   - Click **Create New Project**
   - Name: **Open edX** (or any name you prefer)
   - Click **Continue**

4. Create a new Application:
   - In your project, click **New Application**
   - **Name**: `Open edX App` (must not be empty)
   - **Type**: Select **User Agent** (Web Application)
   - Click **Continue**

5. Configure Authentication:
   - **Authentication Method**: Select **Code** (OIDC)
   - Click **Continue**

6. Configure Redirect URIs:
   - **Redirect URIs**: Add these URIs (replace YOUR_OPENEDX_DOMAIN):
     - `http://YOUR_OPENEDX_DOMAIN/auth/complete/oidc/`
     - `http://YOUR_OPENEDX_DOMAIN/oauth2/redirect`
   - **Post Logout URIs**: 
     - `http://YOUR_OPENEDX_DOMAIN/logout`
   - Click **Continue**

7. Review and Create:
   - Review the settings
   - Click **Create**

8. Get Credentials:
   - After creation, you'll see the application details
   - Note the **Client ID**
   - Click **Regenerate Secret** to get a Client Secret
   - Copy and save both values

## Step 3: (Optional) Add SMS OTP with Kavenegar

**Note**: For basic Open edX integration, SMS OTP is not required. You can skip this section and use standard username/password login.

If you want to add SMS OTP authentication:

### Method 1: Using Default Settings (Easier)

1. In Zitadel Console, go to **Settings** → **Login Policy**
2. Enable **Passwordless with security key**
3. Enable **OTP (Email)** or **OTP (SMS)**
4. Configure SMS provider settings if using SMS OTP

### Method 2: Using Actions (Advanced)

If Actions are available in your Zitadel instance:

1. Go to **Settings** → **Actions** (if available)
2. Click **Add Action**
3. Select trigger: **Post Authentication**
4. Add your action code:

```javascript
function postAuthentication(ctx, api) {
    // Check if this is Open edX login
    if (ctx.request.applicationId === 'YOUR_OPENEDX_CLIENT_ID') {
        // Require additional factor
        api.v1.requireMFA();
    }
}
```

### Method 3: Enable Built-in MFA

The simplest approach is to use Zitadel's built-in MFA:

1. Go to **Settings** → **Security Policy**
2. Under **Multi-Factor Authentication**, enable:
   - **OTP Email** (sends code via email)
   - **OTP SMS** (requires SMS provider setup)
3. Set **MFA Policy**: Required or Optional

### Configure SMS Provider for Built-in SMS OTP

1. Go to **Settings** → **SMS Provider**
2. Add provider details:
   - **Provider**: Custom
   - **Webhook URL**: Create a simple webhook that calls Kavenegar
   - Or use Twilio if supported

### Simple Webhook for Kavenegar (if needed):

```javascript
import { http } from "zitadel";

export async function sendSMSOTP(ctx, event) {
    const phone = event.userPhoneNumber;
    const code = event.otp;
    const apiKey = "YOUR_KAVENEGAR_API_KEY"; // Replace this
    const sender = "30008077778888";

    await http.post({
        url: `https://api.kavenegar.com/v1/${apiKey}/sms/send.json`,
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: `receptor=${phone}&sender=${sender}&message=Your OTP is ${code}`
    });
}
```

**Note**: SMS OTP adds complexity. For simpler integration, you can skip this step and use only username/password authentication.

## Step 4: Configure Open edX with Tutor

### Create Tutor Plugin

Create file `$(tutor config printroot)/plugins/zitadel_oauth2.py`:

```python
from tutor import hooks

# Update these values
ZITADEL_DOMAIN = "http://YOUR_SERVER_IP:8090"  # Your Zitadel URL
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

**Application Invalid Error (PROJECT-1n8df)**: This occurs when creating an application without all required fields:
- Make sure to give the application a name (not empty)
- Select "User Agent" as the type for web applications
- Select "Code" for OIDC authentication
- Add at least one redirect URI

**Domain Invalid Character Error**: Zitadel requires a valid domain format. Use `localhost` in ZITADEL_EXTERNALDOMAIN, not an IP address. You can still access it via `http://YOUR_IP:8090`.

**Port Already in Use**: If port 8090 is also in use, change the port mapping in docker-compose.yml (e.g., `9090:8080`).

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

**Can't Find Flows Menu**: 
- Flows might not be available in all Zitadel versions
- Use **Settings** → **Login Policy** or **Security Policy** instead
- Enable built-in MFA options for simpler setup

**SMS OTP Issues**: 
- Make sure to replace `YOUR_KAVENEGAR_API_KEY` with your actual API key
- Ensure users have verified phone numbers in Zitadel
- Check Zitadel logs for action execution errors
- Consider using built-in OTP Email if SMS setup is complex

That's it! Zitadel is now integrated with Open edX.