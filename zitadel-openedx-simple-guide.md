# Zitadel Self-Hosted with Open edX Integration and SMS OTP (Simplified)

This guide provides a streamlined approach to setting up Zitadel with Open edX using Tutor plugin and native Zitadel actions for SMS OTP via Kavenegar.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setting Up Zitadel with Docker Compose](#setting-up-zitadel-with-docker-compose)
3. [Configuring SMS OTP in Zitadel Actions](#configuring-sms-otp-in-zitadel-actions)
4. [Installing Open edX Tutor Plugin](#installing-open-edx-tutor-plugin)
5. [Configuration Steps](#configuration-steps)
6. [Testing the Integration](#testing-the-integration)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker and Docker Compose installed
- Domain with SSL certificates
- Open edX instance with Tutor
- Kavenegar account with API key
- Basic knowledge of Docker and Tutor

## Setting Up Zitadel with Docker Compose

### 1. Create Directory Structure

```bash
mkdir -p zitadel-setup/{config,certs}
cd zitadel-setup
```

### 2. Create Docker Compose Configuration

Create `docker-compose.yml`:

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

### 3. Create Environment Configuration

Create `.env`:

```bash
# Generate secure keys
ZITADEL_MASTERKEY=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 32)
```

### 4. Create Initial Configuration

Create `config/instance-config.yaml`:

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

### 5. Start Zitadel

```bash
docker-compose up -d
```

## Configuring SMS OTP in Zitadel Actions

### 1. Access Zitadel Console

Navigate to `https://auth.yourdomain.com` and login with admin credentials.

### 2. Create SMS OTP Action

Go to **Actions** → **Create Action** and add:

**Action Name**: `sendSMSOTP`
**Trigger**: Post Authentication

```javascript
import { http } from "zitadel";

// Kavenegar configuration
const KAVENEGAR_API_KEY = "YOUR_KAVENEGAR_API_KEY"; // Replace with your API key
const KAVENEGAR_SENDER = "10004346"; // Your Kavenegar sender number
const OPENEDX_CLIENT_ID = "YOUR_OPENEDX_CLIENT_ID"; // Will get this after creating the app

export async function sendSMSOTP(ctx, api) {
    // Check if this is an Open edX login
    if (ctx.v1.authRequest?.clientId !== OPENEDX_CLIENT_ID) {
        return; // Skip OTP for other applications
    }
    
    // Check if user has verified phone
    const phone = ctx.v1.user?.phone;
    if (!phone || !ctx.v1.user?.phoneVerified) {
        // Optionally, you can require phone verification
        api.v1.user.setMetadata("otp_status", "phone_missing");
        return;
    }
    
    // Generate OTP code
    const code = Math.floor(100000 + Math.random() * 900000).toString();
    
    // Store OTP in user metadata with expiry
    const expiresAt = new Date();
    expiresAt.setMinutes(expiresAt.getMinutes() + 5); // 5 minutes expiry
    
    api.v1.user.setMetadata("otp_code", code);
    api.v1.user.setMetadata("otp_expires", expiresAt.toISOString());
    api.v1.user.setMetadata("otp_attempts", "0");
    
    // Format phone for Kavenegar (remove + if present)
    const formattedPhone = phone.replace(/^\+/, '');
    
    // Send SMS via Kavenegar
    try {
        const response = await http.post({
            url: `https://api.kavenegar.com/v1/${KAVENEGAR_API_KEY}/sms/send.json`,
            headers: { 
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            },
            body: `receptor=${formattedPhone}&sender=${KAVENEGAR_SENDER}&message=Your verification code is: ${code}`
        });
        
        api.v1.user.setMetadata("otp_status", "sent");
        
        // Require MFA verification
        api.v1.authentication.require2FA();
        
    } catch (error) {
        console.error("Failed to send SMS:", error);
        api.v1.user.setMetadata("otp_status", "send_failed");
    }
}
```

### 3. Create OTP Verification Action

Create another action:

**Action Name**: `verifyOTP`
**Trigger**: Post Authentication

```javascript
export async function verifyOTP(ctx, api) {
    // Check if OTP verification is pending
    const otpStatus = ctx.v1.user?.metadata?.otp_status;
    if (otpStatus !== "sent") {
        return;
    }
    
    // Get stored OTP details
    const storedCode = ctx.v1.user?.metadata?.otp_code;
    const expiresAt = ctx.v1.user?.metadata?.otp_expires;
    const attempts = parseInt(ctx.v1.user?.metadata?.otp_attempts || "0");
    
    // Check if OTP exists
    if (!storedCode || !expiresAt) {
        api.v1.authentication.deny("OTP not found");
        return;
    }
    
    // Check expiry
    if (new Date() > new Date(expiresAt)) {
        api.v1.user.removeMetadata("otp_code");
        api.v1.user.removeMetadata("otp_expires");
        api.v1.user.setMetadata("otp_status", "expired");
        api.v1.authentication.deny("OTP expired");
        return;
    }
    
    // Check attempts
    if (attempts >= 3) {
        api.v1.user.removeMetadata("otp_code");
        api.v1.user.removeMetadata("otp_expires");
        api.v1.user.setMetadata("otp_status", "too_many_attempts");
        api.v1.authentication.deny("Too many failed attempts");
        return;
    }
    
    // Get user input (this would come from Zitadel's MFA prompt)
    const userCode = ctx.v1.mfa?.otpCode;
    
    if (userCode === storedCode) {
        // Success - clean up metadata
        api.v1.user.removeMetadata("otp_code");
        api.v1.user.removeMetadata("otp_expires");
        api.v1.user.removeMetadata("otp_attempts");
        api.v1.user.setMetadata("otp_status", "verified");
        api.v1.user.setMetadata("otp_verified_at", new Date().toISOString());
        
        // Allow authentication to proceed
        api.v1.authentication.allow();
    } else {
        // Failed attempt
        api.v1.user.setMetadata("otp_attempts", (attempts + 1).toString());
        api.v1.authentication.deny("Invalid OTP code");
    }
}
```

### 4. Create Action Flow

In Zitadel Console:

1. Go to **Flows** → **Login**
2. Add actions in order:
   - `sendSMSOTP` - Post Authentication
   - `verifyOTP` - Post Authentication

## Installing Open edX Tutor Plugin

### 1. Create Tutor Plugin

Create file `$(tutor config printroot)/plugins/zitadel_oauth2.py`:

```python
"""
Tutor plugin for Zitadel OAuth2/OIDC integration with Open edX
This plugin enables Zitadel authentication for Open edX with automatic account creation.
"""
from tutor import hooks

# ===== LMS CONFIGURATION =====
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# ===== ZITADEL OAUTH2 CONFIGURATION =====
# Enable third party authentication
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
FEATURES["ENABLE_COMBINED_LOGIN_REGISTRATION"] = True
FEATURES["ALLOW_PUBLIC_ACCOUNT_CREATION"] = True

# Add OAuth2 backend
THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# OAuth2 Provider Configuration - IMPORTANT: Replace these values
SOCIAL_AUTH_ZITADEL_KEY = "YOUR_CLIENT_ID"  # Replace with your Client ID from Zitadel
SOCIAL_AUTH_ZITADEL_SECRET = "YOUR_CLIENT_SECRET"  # Replace with your Client Secret from Zitadel
SOCIAL_AUTH_ZITADEL_ENDPOINT = "https://auth.yourdomain.com"  # Your Zitadel URL

# OpenID Connect settings
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = SOCIAL_AUTH_ZITADEL_ENDPOINT
SOCIAL_AUTH_OIDC_KEY = SOCIAL_AUTH_ZITADEL_KEY
SOCIAL_AUTH_OIDC_SECRET = SOCIAL_AUTH_ZITADEL_SECRET

# Add to authentication backends
AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

# Social auth pipeline with Open edX specific handlers
SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'common.djangoapps.third_party_auth.pipeline.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'common.djangoapps.third_party_auth.pipeline.set_logged_in_cookies',
    'common.djangoapps.third_party_auth.pipeline.login_analytics',
]

# Additional settings for Zitadel integration
SOCIAL_AUTH_OIDC_USERNAME_KEY = "preferred_username"
SOCIAL_AUTH_OIDC_EMAIL_KEY = "email"
SOCIAL_AUTH_OIDC_FULLNAME_KEY = "name"

# Map OIDC claims to user fields
SOCIAL_AUTH_OIDC_USERINFO_TO_EXTRA_DATA = [
    "email",
    "preferred_username",
    "name",
    "given_name",
    "family_name",
    "phone",
    "phone_verified"
]

# Allow account linking by email
SOCIAL_AUTH_ASSOCIATE_BY_EMAIL = True

# Auto-create accounts for new users
SOCIAL_AUTH_AUTO_CREATE_USERS = True

# Skip email verification for OAuth users
SKIP_EMAIL_VERIFICATION = True

# Don't require existing account for OAuth
SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False

# Enable third party auth account linking
THIRD_PARTY_AUTH = {
    "ENABLE_THIRD_PARTY_AUTH": True,
    "ENABLE_AUTO_LINK_ACCOUNTS": True,
}

# Force provider to be primary
THIRD_PARTY_AUTH_ONLY_PROVIDER = "oidc"
THIRD_PARTY_AUTH_HINT = "oidc"

# CORS settings for Zitadel
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "https://auth.yourdomain.com",
]

# Set the backend name for the login button
SOCIAL_AUTH_OIDC_CUSTOM_NAME = "Zitadel"

# Make provider visible on login page
THIRD_PARTY_AUTH_PROVIDERS = [{
    "id": "oidc",
    "name": "Zitadel",
    "iconClass": "fa-sign-in",
    "loginUrl": "/auth/login/oidc/?auth_entry=register",
    "registerUrl": "/auth/login/oidc/?auth_entry=register"
}]

# Enable provider display
THIRD_PARTY_AUTH_ENABLE_THIRD_PARTY_AUTH = True
THIRD_PARTY_AUTH_SHOW_IN_LOGIN_PAGE = True
"""
    )
)

# ===== CMS CONFIGURATION =====
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-cms-common-settings",
        """
# ===== ZITADEL OAUTH2 CONFIGURATION FOR CMS =====
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
FEATURES["ALLOW_PUBLIC_ACCOUNT_CREATION"] = True

THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# Use the same OAuth2 settings as LMS
SOCIAL_AUTH_ZITADEL_KEY = "YOUR_CLIENT_ID"  # Same as LMS
SOCIAL_AUTH_ZITADEL_SECRET = "YOUR_CLIENT_SECRET"  # Same as LMS
SOCIAL_AUTH_ZITADEL_ENDPOINT = "https://auth.yourdomain.com"

SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = SOCIAL_AUTH_ZITADEL_ENDPOINT
SOCIAL_AUTH_OIDC_KEY = SOCIAL_AUTH_ZITADEL_KEY
SOCIAL_AUTH_OIDC_SECRET = SOCIAL_AUTH_ZITADEL_SECRET

AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

# Don't require existing account for OAuth
SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False

# CORS settings for CMS
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "https://auth.yourdomain.com",
]
"""
    )
)

# ===== MFE CONFIGURATION =====
hooks.Filters.ENV_PATCHES.add_item(
    (
        "mfe-lms-production-settings",
        """
# Enable third party auth in MFE
ENABLE_THIRD_PARTY_AUTH = True

# Configure OAuth2 provider settings for MFE
OAUTH2_PROVIDER_URL = "/oauth2"
MFE_CONFIG_AUTHN_LOGIN_REDIRECT_URL = "/dashboard"
"""
    )
)

# Add MFE environment variables
hooks.Filters.CONFIG_OVERRIDES.add_item(
    (
        "mfe",
        {
            "ENABLE_THIRD_PARTY_AUTH": True,
            "AUTHN_MINIMAL_HEADER": False,
            "DISABLE_ENTERPRISE_LOGIN": True,
            "SHOW_CONFIGURABLE_EDX_FIELDS": False,
            "THIRD_PARTY_AUTH_ONLY_HINT": "oidc"
        }
    )
)
```

### 2. Enable the Plugin

```bash
tutor plugins enable zitadel_oauth2
tutor config save
tutor images build openedx
tutor images build mfe
tutor local restart
```

## Configuration Steps

### 1. Create OAuth2 Application in Zitadel

1. Login to Zitadel Console
2. Go to **Projects** → Create new project "Open edX"
3. Click **New Application**:
   - Name: `Open edX`
   - Type: `Web Application`
   - Authentication: `OIDC`
4. Configure:
   - Grant Types: `Authorization Code`, `Refresh Token`
   - Redirect URIs: 
     - `https://your-openedx-domain.com/auth/complete/oidc/`
   - Post Logout URI: `https://your-openedx-domain.com/logout`
5. Save and note the **Client ID** and **Client Secret**

### 2. Update Zitadel Actions with Client ID

Go back to your SMS OTP action and update the `OPENEDX_CLIENT_ID` with the actual client ID you just created.

### 3. Update Tutor Plugin

Edit the plugin file and replace:
- `YOUR_CLIENT_ID` with your Zitadel client ID
- `YOUR_CLIENT_SECRET` with your Zitadel client secret
- `https://auth.yourdomain.com` with your Zitadel URL

### 4. Configure Provider in Django Admin

1. Access Django Admin: `https://your-openedx-domain.com/admin`
2. Navigate to **Third Party Auth** → **OAuth2 Provider Config**
3. Add new provider:
   - Name: `oidc`
   - Slug: `oidc`
   - Backend name: `social_core.backends.open_id_connect.OpenIdConnectAuth`
   - Client ID: (your Zitadel client ID)
   - Client Secret: (your Zitadel client secret)
   - Skip registration form: ✓
   - Skip email verification: ✓
   - Visible: ✓
   - Enabled: ✓
   - Icon class: `fa-sign-in`
   - Secondary: ✗ (unchecked)

## Testing the Integration

### 1. Test Basic Login

1. Navigate to: `https://your-openedx-domain.com/login`
2. Click "Sign in with Zitadel"
3. Login with Zitadel credentials
4. You should be redirected to Open edX dashboard

### 2. Test SMS OTP

1. Ensure user has phone number in Zitadel
2. Login via Open edX
3. You should receive SMS with OTP code
4. Enter the code when prompted
5. Successfully login to Open edX

### 3. Direct OAuth URL

For testing: `https://your-openedx-domain.com/auth/login/oidc/?auth_entry=register&next=/dashboard`

## Troubleshooting

### Common Issues

1. **No SMS Received**
   - Check Kavenegar API key in action
   - Verify phone number format (international)
   - Check Zitadel logs for action errors

2. **OAuth Error**
   - Verify redirect URIs match exactly
   - Check client secret is correct
   - Ensure HTTPS is configured

3. **403 Forbidden**
   - Ensure user email is verified in Zitadel
   - Check SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False

4. **Action Not Triggering**
   - Verify action is added to Login flow
   - Check client ID matches in action
   - Review Zitadel execution logs

### Debug Mode

Add to Tutor plugin for debugging:
```python
SOCIAL_AUTH_OIDC_DEBUG = True
LOGGING['handlers']['console']['level'] = 'DEBUG'
```

### Logs

- Zitadel logs: `docker-compose logs zitadel`
- Open edX logs: `tutor local logs lms`
- Action logs: Check in Zitadel Console → Actions → Executions

## Security Best Practices

1. **Use HTTPS everywhere**
2. **Rotate secrets regularly**
3. **Limit OTP attempts** (already in action)
4. **Set OTP expiry** (5 minutes in action)
5. **Verify phone numbers** in Zitadel
6. **Use strong passwords** for admin accounts
7. **Regular backups** of PostgreSQL

## Additional Resources

- [Zitadel Actions Documentation](https://zitadel.com/docs/guides/integrate/actions)
- [Tutor Plugin Development](https://docs.tutor.overhang.io/tutorials/plugin.html)
- [Kavenegar API Docs](https://kavenegar.com/rest.html)
- [Open edX Third Party Auth](https://edx.readthedocs.io/projects/edx-installing-configuring-and-running/en/latest/configuration/tpa/)