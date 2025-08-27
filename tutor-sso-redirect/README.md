# Tutor SSO Redirect Plugin

This plugin configures Open edX to redirect to the MFE authentication page first, which then automatically redirects to your SSO provider (Zitadel).

## What This Fixes

- **Legacy Open edX** (localhost:8000) redirects to MFE for login
- **MFE** automatically redirects to SSO (Zitadel)
- Maintains proper authentication flow: Legacy → MFE → SSO
- Auto-redirect from MFE to SSO provider
- Fixes "Can't fetch setting of a disabled backend/provider" error

## Quick Installation

```bash
# 1. Install the plugin
pip install -e /path/to/tutor-sso-redirect

# 2. Enable it
tutor plugins enable sso-redirect

# 3. Configure your Zitadel credentials
tutor config save --set SSO_OIDC_KEY="your-client-id@projectname"
tutor config save --set SSO_OIDC_SECRET="your-client-secret"
tutor config save --set SSO_OIDC_ENDPOINT="https://your-zitadel-instance.zitadel.cloud"

# 4. Save and restart
tutor config save
tutor local restart
```

## CRITICAL: Configure OIDC in Django Admin

**This step is required or you'll get "Can't fetch setting of a disabled backend/provider"**

1. Access Django admin at http://localhost:8000/admin
2. Go to **Third Party Auth** → **OAuth2 Provider Configs**
3. Add a new config with:
   - **Enabled**: ✓
   - **Name**: `oidc` (MUST be exactly 'oidc')
   - **Slug**: `oidc` 
   - **Backend name**: `social_core.backends.open_id_connect.OpenIdConnectAuth`
   - **Client ID**: Your Zitadel client ID
   - **Client Secret**: Your Zitadel client secret
   - **Other settings**:
     ```json
     {
       "OIDC_ENDPOINT": "https://your-zitadel-instance.zitadel.cloud"
     }
     ```

See [ZITADEL_SETUP.md](ZITADEL_SETUP.md) for detailed Zitadel configuration.

## How It Works

1. **Enables authn MFE** with proper configuration:
   - `AUTHN_MICROFRONTEND_URL = "http://apps.local.openedx.io:1999/authn"`
   - `ENABLE_AUTHN_MICROFRONTEND = True`

2. **Enables OIDC backend** with proper authentication settings

3. **Auto-redirect from MFE to SSO** using:
   - `AUTHN_REDIRECT_TO_OIDC = True`
   - `AUTHN_DEFAULT_REDIRECT_URL = '/auth/login/oidc/'`

4. **Proper authentication flow**: Legacy → MFE → Zitadel

## Testing

Test both legacy and MFE routes:

```bash
python test_both_routes.py http://localhost:8000 http://apps.local.openedx.io:1999
```

Expected output:
```
Legacy login: http://localhost:8000/login
  ✓ CORRECT - Redirects to SSO

Legacy register: http://localhost:8000/register
  ✓ CORRECT - Redirects to SSO

MFE authn login: http://apps.local.openedx.io:1999/authn/login
  ✓ CORRECT - Redirects to SSO
```

## URLs That Get Redirected

ALL of these go directly to your SSO:

### Legacy URLs
- `/login`
- `/register`
- `/signin`
- `/signup`
- `/user_api/v1/account/login_session/`

### MFE URLs
- `/authn/login`
- `/authn/register`
- `/authn/logistration`

### Any URL containing
- `login`
- `signin`
- `register`
- `signup`

## Troubleshooting

### "Can't fetch setting of a disabled backend/provider"

You need to configure the OIDC provider in Django admin. See the "Configure OIDC in Django Admin" section above.

### Still redirecting to MFE?

1. Clear your browser cache
2. Check the logs:
   ```bash
   tutor local logs -f lms | grep "SSO Redirect"
   ```
3. Verify MFE is disabled:
   ```bash
   tutor local exec lms python /openedx/check_middleware.py
   ```

### Redirect loops?

Check your Zitadel redirect URLs include:
- `http://localhost:8000/auth/complete/oidc/`
- `http://localhost:8001/auth/complete/oidc/`
- `http://apps.local.openedx.io:1999/auth/complete/oidc/`

## License

AGPLv3