# Zitadel + Open edX - Simplest Setup Guide

This guide uses Open edX's built-in OIDC support - no custom backends needed!

## Why This Works

Open edX already includes `social_core.backends.open_id_connect.OpenIdConnectAuth` which supports any standard OIDC provider. Zitadel is OIDC-compliant, so it works out of the box.

## Step 1: Setup Zitadel

```bash
# Quick setup
docker-compose -f docker-compose-simple.yml up -d
```

## Step 2: Create OAuth App in Zitadel

1. Login to Zitadel Console
2. Create Project → Create Application (Web, OIDC)
3. Set Redirect URI: `https://your-openedx.com/auth/complete/oidc/`
4. Note the Client ID and Secret

## Step 3: Configure Open edX with Tutor

### Option A: Using the Plugin (Recommended)

```bash
# Copy plugin
cp zitadel_oauth2_builtin.py $(tutor config printroot)/plugins/zitadel_oauth2.py

# Edit plugin - update these 3 lines:
ZITADEL_DOMAIN = "https://auth.yourdomain.com"
ZITADEL_CLIENT_ID = "your-client-id"
ZITADEL_CLIENT_SECRET = "your-client-secret"

# Enable and rebuild
tutor plugins enable zitadel_oauth2
tutor config save
tutor images build openedx
tutor local restart
```

### Option B: Manual Configuration

Add to your `$(tutor config printroot)/env/apps/openedx/settings/lms/production.py`:

```python
# Enable third party auth
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True

# Use built-in OIDC backend
THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# Zitadel configuration
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = "https://auth.yourdomain.com"
SOCIAL_AUTH_OIDC_KEY = "your-client-id"
SOCIAL_AUTH_OIDC_SECRET = "your-client-secret"

# Add to authentication backends
AUTHENTICATION_BACKENDS = [
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
] + list(AUTHENTICATION_BACKENDS)

# Allow auto account creation
SOCIAL_AUTH_REQUIRE_EXISTING_ACCOUNT = False
```

## Step 4: Configure in Django Admin

1. Go to `https://your-openedx.com/admin`
2. Navigate to **Third Party Auth** → **OAuth2 Provider Config**
3. Add new provider:
   - **Name**: oidc
   - **Slug**: oidc  
   - **Backend name**: `social_core.backends.open_id_connect.OpenIdConnectAuth`
   - **Client ID**: (from Zitadel)
   - **Client Secret**: (from Zitadel)
   - **Enabled**: ✓

## Step 5: Add SMS OTP (Optional)

In Zitadel Console:
1. Go to **Actions** → Create Action
2. Add the SMS OTP action from `config/zitadel-sms-otp-kavenegar.js`
3. Update `KAVENEGAR_API_KEY` and `OPENEDX_CLIENT_ID`
4. Add to Login Flow

## That's It!

Test login at:
- `https://your-openedx.com/login`
- Direct: `https://your-openedx.com/auth/login/oidc/`

## Why No Custom Backend?

The built-in `OpenIdConnectAuth` backend already:
- Handles OIDC discovery
- Maps standard claims (email, name, username)
- Creates user accounts
- Updates user details

Zitadel provides standard OIDC claims:
- `preferred_username` → username
- `email` → email
- `name` → full name
- `given_name` → first name
- `family_name` → last name

Everything just works!