# MFE Authentication with Zitadel Setup Guide

This guide explains how to configure Open edX to use the Authentication MFE (Micro Frontend) with Zitadel SSO.

## Overview

The authentication flow will work as follows:
1. User visits http://91.107.146.137:8000/ and clicks "Sign In"
2. User is redirected to the MFE at http://apps.local.openedx.io:1999/authn/login
3. MFE automatically redirects to Zitadel for authentication
4. After successful authentication, user returns to MFE
5. MFE completes the login and redirects to the LMS dashboard

## Configuration Steps

### 1. Configure the Plugin

Set the following in your Tutor configuration:

```bash
# Enable MFE mode
tutor config save --set SSO_USE_MFE=true
tutor config save --set SSO_MFE_URL="http://apps.local.openedx.io:1999"

# Keep your existing Zitadel configuration
tutor config save --set SSO_OIDC_KEY="your-client-id@projectname"
tutor config save --set SSO_OIDC_SECRET="your-client-secret"
tutor config save --set SSO_OIDC_ENDPOINT="https://your-zitadel-instance.zitadel.cloud"

# Save configuration
tutor config save
```

### 2. Update Zitadel Redirect URLs

In your Zitadel application, ensure you have these redirect URLs:

```
http://91.107.146.137:8000/auth/complete/oidc/
http://91.107.146.137:8001/auth/complete/oidc/
http://apps.local.openedx.io:1999/auth/complete/oidc/
http://localhost:8000/auth/complete/oidc/
http://localhost:8001/auth/complete/oidc/
```

### 3. Configure MFE Environment

The plugin will automatically configure the MFE to work with Zitadel. The MFE will:
- Show the Zitadel login button
- Hide local registration/login forms
- Automatically redirect to Zitadel

### 4. Rebuild and Restart

```bash
# Rebuild images
tutor images build openedx
tutor images build mfe

# Restart services
tutor local restart
```

### 5. Configure OIDC Provider (if not already done)

Run the configuration script:

```bash
tutor local exec lms python /openedx/configure_oidc_provider.py
```

## Testing the Flow

1. Clear your browser cookies
2. Visit http://91.107.146.137:8000/
3. Click "Sign In"
4. You should be redirected to http://apps.local.openedx.io:1999/authn/login
5. The MFE should show the Zitadel login option
6. Clicking it should take you to Zitadel
7. After authentication, you should return to the MFE and then be redirected to the dashboard

## Troubleshooting

### MFE Not Loading

If the MFE at http://apps.local.openedx.io:1999 is not accessible:

1. Check if MFE is running:
   ```bash
   tutor local status
   ```

2. Check MFE logs:
   ```bash
   tutor local logs -f mfe
   ```

3. Ensure your hosts file has:
   ```
   127.0.0.1 apps.local.openedx.io
   ```

### Authentication Loop

If you get stuck in an authentication loop:

1. Check the browser console for errors
2. Verify all redirect URLs are correct in Zitadel
3. Check LMS logs:
   ```bash
   tutor local logs -f lms | grep -E "SSO|social|oauth|oidc"
   ```

### Direct Zitadel Redirect (Bypass MFE)

If you want to bypass the MFE and go directly to Zitadel:

```bash
tutor config save --set SSO_USE_MFE=false
tutor config save
tutor local restart
```

## Advanced Configuration

### Custom MFE URL

If your MFE is hosted elsewhere:

```bash
tutor config save --set SSO_MFE_URL="https://your-mfe-domain.com"
```

### HTTPS Configuration

For production with HTTPS:

1. Update all URLs to use https://
2. Set in Django settings:
   - SESSION_COOKIE_SECURE = True
   - SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

## Debugging

Run the debug script to check your configuration:

```bash
tutor local exec lms python /openedx/debug_auth_flow.py
```

This will show:
- MFE configuration status
- OIDC provider configuration
- Session settings
- Authentication pipeline