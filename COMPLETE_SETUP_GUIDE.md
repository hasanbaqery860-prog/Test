# Complete Setup Guide: Open edX Teak + Authentik OAuth2

This guide will walk you through setting up Open edX (Teak version) with Authentik authentication from scratch.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Install Open edX using Tutor](#install-open-edx)
3. [Set up Authentik](#setup-authentik)
4. [Install the Authentication Plugin](#install-plugin)
5. [Configure Django Admin](#configure-django)
6. [Test Everything](#test)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites {#prerequisites}

You need:
- A server with at least 8GB RAM and 25GB disk space
- Ubuntu 20.04 or 22.04
- Docker and Docker Compose installed
- A domain name (or use local.openedx.io for testing)

## Step 1: Install Open edX using Tutor {#install-open-edx}

### 1.1 Install Tutor

```bash
# Install Python and pip
sudo apt update
sudo apt install python3 python3-pip curl -y

# Install Tutor
pip3 install "tutor[full]"

# Add to PATH (add this to ~/.bashrc too)
export PATH="$HOME/.local/bin:$PATH"

# Verify installation
tutor --version
```

### 1.2 Configure Tutor for Teak Version

```bash
# Create Tutor directory
mkdir ~/openedx
cd ~/openedx

# Configure Tutor (accept defaults or customize)
tutor config save --interactive

# IMPORTANT: Set the Open edX version to Teak
tutor config save --set OPENEDX_COMMON_VERSION=open-release/teak.master
```

### 1.3 Launch Open edX

```bash
# Pull all Docker images (this takes time)
tutor images pull all

# Launch Open edX
tutor local launch

# Follow the prompts:
# - Press Enter for default platform name
# - Enter your email
# - Create a username and password (REMEMBER THESE!)
```

Wait for "All services ready" message. This takes 10-30 minutes.

### 1.4 Verify Open edX is Running

Open your browser and go to:
- LMS: http://local.openedx.io:8000
- Studio: http://local.openedx.io:8001

## Step 2: Set up Authentik {#setup-authentik}

### 2.1 Install Authentik using Docker Compose

```bash
# Create directory for Authentik
mkdir ~/authentik
cd ~/authentik

# Download docker-compose file
wget https://raw.githubusercontent.com/goauthentik/authentik/main/docker-compose.yml

# Generate passwords
echo "PG_PASS=$(openssl rand -base64 36)" >> .env
echo "AUTHENTIK_SECRET_KEY=$(openssl rand -base64 60)" >> .env
echo "AUTHENTIK_ERROR_REPORTING__ENABLED=false" >> .env

# Start Authentik
docker-compose up -d
```

### 2.2 Initial Authentik Setup

1. Wait 2 minutes, then open: http://localhost:9000/if/flow/initial-setup/
2. Create admin account:
   - Username: `akadmin`
   - Email: your email
   - Password: choose a strong password
3. Click "Continue"

### 2.3 Create OAuth2 Application in Authentik

1. Login to Authentik Admin: http://localhost:9000/if/admin/
2. Go to **Applications → Applications**
3. Click **Create**
4. Fill in:
   - Name: `Open edX`
   - Slug: `openedx`
   - Provider: (we'll create this next)
5. Click **Create**

### 2.4 Create OAuth2 Provider

1. Go to **Applications → Providers**
2. Click **Create → OAuth2/OpenID Provider**
3. Fill in:
   - Name: `openedx-oauth2`
   - Authentication flow: `default-authentication-flow`
   - Authorization flow: `default-provider-authorization-implicit-consent`
   - Client type: `Confidential`
   - Client ID: `openedx-oauth2-client` (COPY THIS!)
   - Client Secret: Click the refresh button to generate (COPY THIS!)
   - Redirect URIs: 
     ```
     http://local.openedx.io:8000/auth/complete/oidc/
     ```
   - Signing Key: `authentik Self-signed Certificate`
4. Under **Advanced protocol settings**:
   - Scopes: Select `email`, `openid`, `profile`
   - Subject mode: `Based on the User's Email`
   - Include claims in id_token: ✓ (checked)
5. Click **Create**

### 2.5 Link Provider to Application

1. Go back to **Applications → Applications**
2. Click on **Open edX**
3. In the Provider dropdown, select `openedx-oauth2`
4. Click **Update**

### 2.6 Enable User Registration in Authentik

1. Go to **Flows & Stages → Flows**
2. Find `default-authentication-flow`
3. Click on it, then click **Stage Bindings**
4. Find the `default-authentication-identification` stage
5. Click **Edit**
6. Enable **Enroll users** 
7. Enable **Show sources**
8. Click **Update**

## Step 3: Install the Authentication Plugin {#install-plugin}

### 3.1 Download the Plugin

```bash
# Go to your home directory
cd ~

# Download the plugin file
wget https://raw.githubusercontent.com/hasanbaqery860-prog/Test/cursor/integrate-authentik-authentication-for-open-edx-5765/authentik_oauth2_complete.py

# Or create it manually
nano authentik_oauth2_complete.py
# Then copy the entire plugin code from the repository
```

### 3.2 Install the Plugin in Tutor

```bash
# Copy plugin to Tutor plugins directory
cp authentik_oauth2_complete.py "$(tutor config printroot)/plugins/authentik_oauth2.py"

# Enable the plugin
tutor plugins enable authentik_oauth2
```

### 3.3 Update the Plugin with Your Credentials

```bash
# Edit the plugin
nano "$(tutor config printroot)/plugins/authentik_oauth2.py"

# Find these lines and update them:
SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY = "openedx-oauth2-client"  # Replace with your Client ID
SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET = "YOUR_CLIENT_SECRET_HERE"  # Replace with your Client Secret
SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT = "http://localhost:9000/application/o/openedx/"  # Update if needed

# Save and exit (Ctrl+X, Y, Enter)
```

### 3.4 Rebuild and Restart Open edX

```bash
# Save configuration
tutor config save

# Rebuild images (this takes time)
tutor images build openedx
tutor images build mfe

# Initialize (this runs the plugin hooks)
tutor local init

# Restart everything
tutor local restart
```

## Step 4: Configure Django Admin {#configure-django}

### 4.1 Create the OAuth2 Provider in Django Admin

1. Go to Django Admin: http://local.openedx.io:8000/admin
2. Login with your Open edX superuser account
3. Go to **Third Party Auth → OAuth2 Provider Configs**
4. Click **Add OAuth2 Provider Config**
5. Fill in EXACTLY:
   - **Name**: `oidc`
   - **Slug**: `oidc`
   - **Site**: Select `local.openedx.io:8000`
   - **Skip hinted login dialog**: ✓ (checked)
   - **Skip registration form**: ✓ (checked) 
   - **Skip email verification**: ✓ (checked)
   - **Visible to unauthenticated users**: ✓ (checked)
   - **Backend name**: `social_core.backends.open_id_connect.OpenIdConnectAuth`
   - **Client ID**: Your Authentik Client ID (e.g., `openedx-oauth2-client`)
   - **Client Secret**: Your Authentik Client Secret
   - **Icon class**: `fa-sign-in`
   - **Enabled**: ✓ (checked)
   - **Secondary**: ❌ (UNCHECKED - VERY IMPORTANT!)
6. Click **Save**

### 4.2 Run the Fix Command

```bash
# This ensures the provider is configured correctly
tutor local exec lms python manage.py lms shell -c "
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
p = OAuth2ProviderConfig.objects.get(backend_name='social_core.backends.open_id_connect.OpenIdConnectAuth')
p.secondary = False
p.visible_for_unauthenticated_users = True
p.enabled = True
p.save()
from django.core.cache import cache
cache.clear()
print('✅ Provider configured successfully!')"

# Restart services
tutor local restart openedx
```

## Step 5: Test Everything {#test}

### 5.1 Clear Your Browser

1. Clear all cookies for `local.openedx.io`
2. Clear browser cache
3. Or use an incognito/private window

### 5.2 Test Login

1. Go to: http://local.openedx.io:8000/authn/login
2. You should see **"Sign in with Authentik"** button
3. Click it
4. You'll be redirected to Authentik
5. Login with an Authentik account
6. You'll be redirected back to Open edX dashboard

### 5.3 Test Registration

1. Go to: http://local.openedx.io:8000/authn/register  
2. Click **"Sign up with Authentik"**
3. In Authentik, click "Register" or "Sign up" link
4. Create a new account
5. You'll be logged into Open edX automatically

## Step 6: Troubleshooting {#troubleshooting}

### Button Not Showing?

```bash
# Check if provider exists
tutor local exec lms python manage.py lms shell -c "
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
print(OAuth2ProviderConfig.objects.filter(backend_name='social_core.backends.open_id_connect.OpenIdConnectAuth').exists())"

# If False, go back to Django Admin and create it
```

### 403 Error?

```bash
# Fix the provider settings
tutor local exec lms python manage.py lms shell -c "
from common.djangoapps.third_party_auth.models import OAuth2ProviderConfig
p = OAuth2ProviderConfig.objects.get(backend_name='social_core.backends.open_id_connect.OpenIdConnectAuth')
p.secondary = False
p.enabled = True
p.visible_for_unauthenticated_users = True
p.skip_registration_form = True
p.skip_email_verification = True
p.send_to_registration_first = False
p.save()
print('Fixed!')"

tutor local restart openedx
```

### Check MFE Context

Visit: http://local.openedx.io:8000/api/mfe_context?next=%2F

Look for `providers` array - your provider should be there, NOT in `secondaryProviders`.

### View Logs

```bash
# Check for errors
tutor local logs -f lms | grep -i "auth\|error"
```

### Still Not Working?

1. Double-check Client ID and Secret match between Authentik and Open edX
2. Ensure Authentik is accessible from Open edX container:
   ```bash
   tutor local exec lms curl http://host.docker.internal:9000
   ```
3. Check Django Admin - provider must have "Secondary" UNCHECKED

## Appendix: Understanding the Flow

1. User clicks "Sign in with Authentik" on Open edX
2. Open edX redirects to Authentik OAuth2 authorize endpoint
3. User logs in (or registers) on Authentik  
4. Authentik redirects back to Open edX with authorization code
5. Open edX exchanges code for tokens
6. Open edX creates/links user account based on email
7. User is logged into Open edX

## Appendix: Production Considerations

For production:
1. Use HTTPS everywhere
2. Use real domain names, not localhost
3. Set secure passwords and secrets
4. Configure email sending in both systems
5. Set up monitoring and backups
6. Consider using Authentik's advanced features (2FA, policies, etc.)

---

**Congratulations!** You now have Open edX with Authentik authentication working!