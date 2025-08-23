# Tutor SSO Redirect Plugin

This plugin forces BOTH legacy Open edX (localhost:8000) and MFE (apps.local.openedx.io:1999) to redirect directly to your SSO provider (Zitadel), bypassing the authn MFE completely.

## What This Fixes

- **Legacy Open edX** (localhost:8000) no longer redirects to MFE for login
- **Both legacy and MFE** routes go directly to SSO
- No more redirect loops between legacy → MFE → SSO
- Complete bypass of authn MFE

## Quick Installation

```bash
# 1. Install the plugin
pip install -e /path/to/tutor-sso-redirect

# 2. Enable it
tutor plugins enable sso-redirect

# 3. Configure your SSO endpoint (if not using default)
tutor config save --set SSO_REDIRECT_URL="/auth/login/oidc/"

# 4. Save and restart
tutor config save
tutor local restart
```

## How It Works

1. **Completely disables authn MFE** by setting:
   - `AUTHN_MICROFRONTEND_URL = None`
   - `ENABLE_AUTHN_MICROFRONTEND = False`

2. **Aggressive middleware** that intercepts ALL login/register URLs and redirects to SSO

3. **URL overrides** that catch requests before they can redirect to MFE

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