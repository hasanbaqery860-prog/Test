# Quick Start Guide - Tutor SSO Redirect Plugin

## 1. Installation (5 minutes)

```bash
# Install the plugin
pip install -e /path/to/tutor-sso-redirect

# Enable the plugin
tutor plugins enable sso-redirect

# Save configuration
tutor config save
```

## 2. Configure Your SSO Provider (10 minutes)

### For Azure AD:

1. In Azure Portal, create an App Registration
2. Set redirect URI: `https://your-lms-domain/auth/complete/azuread-oauth2/`
3. Copy the Application (client) ID and create a client secret
4. Add to your `config.yml`:

```yaml
SSO_PROVIDER_NAME: "azuread-oauth2"
SOCIAL_AUTH_AZUREAD_OAUTH2_KEY: "your-client-id"
SOCIAL_AUTH_AZUREAD_OAUTH2_SECRET: "your-client-secret"
SOCIAL_AUTH_AZUREAD_OAUTH2_TENANT_ID: "your-tenant-id"
```

### For Keycloak:

1. Create a new client in your Keycloak realm
2. Set redirect URI: `https://your-lms-domain/auth/complete/oidc/`
3. Copy client ID and secret
4. Add to your `config.yml`:

```yaml
SSO_PROVIDER_NAME: "oidc"
SOCIAL_AUTH_OIDC_OIDC_ENDPOINT: "https://keycloak.example.com/auth/realms/your-realm"
SOCIAL_AUTH_OIDC_KEY: "your-client-id"
SOCIAL_AUTH_OIDC_SECRET: "your-client-secret"
```

## 3. Build and Launch (15 minutes)

```bash
# Rebuild images with the middleware
tutor images build openedx

# Launch the platform
tutor local launch
```

## 4. Configure in Django Admin (5 minutes)

1. Go to `https://your-lms-domain/admin`
2. Navigate to **Third Party Auth** → **OAuth2 Provider Config**
3. Click **Add OAuth2 Provider Config**
4. Fill in:
   - **Enabled**: ✓
   - **Provider**: Select your provider
   - **Name**: Display name
   - **Client ID**: Your OAuth client ID
   - **Client Secret**: Your OAuth client secret
   - **Other settings**: Provider-specific settings
5. Save

## 5. Test the Setup

```bash
# Run the test script
python test_redirect.py https://your-lms-domain

# Or manually test:
# 1. Go to https://your-lms-domain/login
# 2. You should be redirected to /auth/login/oidc/
# 3. Complete SSO login
# 4. You should be redirected back to the dashboard
```

## Troubleshooting

### "Page not found" on /auth/login/oidc/

- Ensure third-party auth is enabled in Django admin
- Check that your provider is configured and enabled

### Redirect loops

- Verify your SSO provider's redirect URI matches exactly
- Check logs: `tutor local logs -f lms`

### Users can still see login page

- Clear browser cache
- Restart services: `tutor local restart`
- Verify plugin is enabled: `tutor plugins list`

## Need Help?

- Check the full README.md for detailed documentation
- Review LMS logs for error messages
- Ensure your SSO provider is properly configured