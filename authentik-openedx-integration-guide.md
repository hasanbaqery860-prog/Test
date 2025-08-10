# Authentik and Open edX Integration Guide

This guide will help you integrate Authentik authentication with your Open edX Teak version setup using Tutor.

## Prerequisites
- Open edX Teak version installed with Tutor
- Authentik server running on `localhost:9000`
- LMS accessible at `http://local.openedx.io:8000/`
- Studio accessible at `http://studio.local.openedx.io:8001/`

## Part 1: Authentik Configuration

### Step 1: Create OAuth2/OpenID Connect Provider in Authentik

1. **Login to Authentik** at `http://localhost:9000`

2. **Create an OAuth2/OpenID Provider:**
   - Navigate to **Applications** → **Providers**
   - Click **Create**
   - Select **OAuth2/OpenID Provider**
   - Configure as follows:
     ```
     Name: Open edX Provider
     Authorization flow: default-provider-authorization-implicit-consent
     Client type: Confidential
     Client ID: openedx-oauth2-client (save this)
     Client Secret: (auto-generated, save this)
     Redirect URIs: 
       http://local.openedx.io:8000/auth/complete/authentik-oauth2/
       http://studio.local.openedx.io:8001/auth/complete/authentik-oauth2/
     Signing Key: authentik Self-signed Certificate
     ```

3. **Configure Scopes:**
   - In the provider settings, ensure these scopes are selected:
     - `openid`
     - `email`
     - `profile`

4. **Create an Application:**
   - Navigate to **Applications** → **Applications**
   - Click **Create**
   - Configure:
     ```
     Name: Open edX
     Slug: openedx
     Provider: Open edX Provider (the one you just created)
     Launch URL: http://local.openedx.io:8000/
     ```

### Step 2: Configure Property Mappings (if needed)

Authentik should have default property mappings for OIDC, but verify:
- Navigate to **Customization** → **Property Mappings**
- Ensure you have mappings for:
  - `email`
  - `name`
  - `given_name`
  - `family_name`
  - `preferred_username`

## Part 2: Open edX Configuration

### Step 3: Create a Tutor Plugin for OAuth2 Configuration

Create a custom Tutor plugin to configure OAuth2 without modifying core files:

1. **Create plugin directory:**
   ```bash
   mkdir -p $(tutor config printroot)/plugins
   ```

2. **Create the plugin file:**
   ```bash
   nano $(tutor config printroot)/plugins/authentik_oauth2.py
   ```

3. **Add the following content to the plugin:**

```python
from tutor import hooks

# OAuth2 configuration for Authentik
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# Authentik OAuth2 Configuration
THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

# Enable third party auth
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
FEATURES["ENABLE_COMBINED_LOGIN_REGISTRATION"] = True

# OAuth2 Provider Configuration
SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY = "openedx-oauth2-client"  # Replace with your Client ID
SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET = "YOUR_CLIENT_SECRET_HERE"  # Replace with your Client Secret
SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT = "http://localhost:9000/application/o/openedx/"

# OpenID Connect settings
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT
SOCIAL_AUTH_OIDC_KEY = SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY
SOCIAL_AUTH_OIDC_SECRET = SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET

# Backend name
AUTHENTICATION_BACKENDS = (
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
) + AUTHENTICATION_BACKENDS

# Pipeline configuration
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)
"""
    )
)

# Add the same configuration for CMS
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-cms-common-settings",
        """
# Authentik OAuth2 Configuration for CMS
THIRD_PARTY_AUTH_BACKENDS = ["social_core.backends.open_id_connect.OpenIdConnectAuth"]

FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True

SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY = "openedx-oauth2-client"  # Replace with your Client ID
SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET = "YOUR_CLIENT_SECRET_HERE"  # Replace with your Client Secret
SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT = "http://localhost:9000/application/o/openedx/"

SOCIAL_AUTH_OIDC_OIDC_ENDPOINT = SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT
SOCIAL_AUTH_OIDC_KEY = SOCIAL_AUTH_AUTHENTIK_OAUTH2_KEY
SOCIAL_AUTH_OIDC_SECRET = SOCIAL_AUTH_AUTHENTIK_OAUTH2_SECRET

AUTHENTICATION_BACKENDS = (
    "social_core.backends.open_id_connect.OpenIdConnectAuth",
) + AUTHENTICATION_BACKENDS
"""
    )
)
```

### Step 4: Alternative Method - Using Third Party Auth in Django Admin

If you prefer to configure through the Django admin interface instead of using the plugin:

1. **Create a superuser (if not exists):**
   ```bash
   tutor local run lms ./manage.py lms createsuperuser
   ```

2. **Access Django Admin:**
   - Navigate to `http://local.openedx.io:8000/admin`
   - Login with your superuser credentials

3. **Enable Third Party Auth Feature:**
   - Go to **Site Configuration** → **Site configurations**
   - Click on the site configuration for your domain (or create one)
   - In the `values` field, ensure you have:
   ```json
   {
     "ENABLE_THIRD_PARTY_AUTH": true,
     "ENABLE_COMBINED_LOGIN_REGISTRATION": true
   }
   ```

4. **Configure OAuth2 Provider:**
   - Go to **Third Party Auth** → **Provider Configuration (OAuth)**
   - Click **Add Provider Configuration**
   - Fill in the following:
     ```
     ✓ Enabled
     ✓ Skip registration form
     ✓ Skip email verification
     Name: Authentik
     Slug: oidc
     Site: [Select your site]
     Backend name: social_core.backends.open_id_connect.OpenIdConnectAuth
     Client ID: openedx-oauth2-client
     Client Secret: YOUR_CLIENT_SECRET_HERE
     Other settings:
     {
       "OIDC_ENDPOINT": "http://localhost:9000/application/o/openedx/"
     }
     ```
   - Click **Save**

5. **Configure Provider Site Association:**
   - Go to **Third Party Auth** → **Provider Configuration (SAML/OAuth) to Site Associations**
   - Click **Add**
   - Select your provider and site
   - Click **Save**

### Step 5: Configure Site Configuration

1. **Update site configuration:**
   ```bash
   tutor local run lms ./manage.py lms shell
   ```

2. **In the Python shell:**
   ```python
   from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
   site_config, created = SiteConfiguration.objects.get_or_create(
       site_id=1,
       defaults={
           'enabled': True,
           'values': {}
       }
   )
   
   site_config.values.update({
       "ENABLE_THIRD_PARTY_AUTH": True,
       "ENABLE_COMBINED_LOGIN_REGISTRATION": True,
       "THIRD_PARTY_AUTH_HINT": "authentik-oauth2"
   })
   site_config.save()
   ```

### Step 6: Enable and Rebuild

1. **Enable the plugin:**
   ```bash
   tutor plugins enable authentik_oauth2
   ```

2. **Save configuration:**
   ```bash
   tutor config save
   ```

3. **Rebuild Open edX images:**
   ```bash
   tutor images build openedx
   ```

4. **Restart services:**
   ```bash
   tutor local stop
   tutor local start -d
   ```

## Part 3: Testing the Integration

1. **Test Login Flow:**
   - Navigate to `http://local.openedx.io:8000/login`
   - You should see an option to "Sign in with Authentik"
   - Click it and you'll be redirected to Authentik
   - After authentication, you'll be redirected back to Open edX

2. **Verify User Creation:**
   - Check Django admin to see if user was created
   - Verify email and profile information was populated

## Troubleshooting

### Common Issues:

1. **Redirect URI Mismatch:**
   - Ensure redirect URIs in Authentik match exactly
   - Check for http vs https
   - Verify port numbers

2. **CORS Issues:**
   - Add CORS headers in Tutor plugin:
   ```python
   CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
       "http://localhost:9000",
   ]
   ```

3. **SSL/TLS Issues:**
   - For production, use HTTPS for all services
   - Update URLs accordingly

4. **User Mapping Issues:**
   - Verify Authentik is sending required claims
   - Check property mappings in Authentik
   - Enable debug logging:
   ```python
   SOCIAL_AUTH_OIDC_DEBUG = True
   ```

## Files Modified Summary

1. **Created new plugin file:**
   - `$(tutor config printroot)/plugins/authentik_oauth2.py`

2. **No core Open edX files modified** - all configuration done through:
   - Tutor plugin system
   - Django admin interface
   - Site configuration

This approach ensures minimal changes to Open edX core code while leveraging existing OAuth2/OIDC functionality.