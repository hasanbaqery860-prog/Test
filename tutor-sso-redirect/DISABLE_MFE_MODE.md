# Disable MFE Mode - Use Direct SSO

Since the MFE is showing an empty page at `/login`, you can disable MFE mode and use direct SSO redirection to Zitadel.

## Quick Fix - Disable MFE Mode

Run these commands:

```bash
# Disable MFE mode (use direct SSO)
tutor config save --set SSO_USE_MFE=false

# Save configuration
tutor config save

# Restart services
tutor local restart
```

## What This Does

With `SSO_USE_MFE=false`, the plugin will:
1. Completely disable the Authentication MFE
2. Redirect all login attempts directly to Zitadel
3. After Zitadel authentication, return directly to Open edX

## Authentication Flow (Direct Mode)

1. User visits http://91.107.146.137:8000/ and clicks "Sign In"
2. Plugin redirects directly to Zitadel (bypassing MFE)
3. User authenticates with Zitadel
4. Zitadel redirects back to http://91.107.146.137:8000/auth/complete/oidc/
5. User is logged in and redirected to dashboard

## Verify It's Working

After making the change:

1. Clear your browser cookies
2. Visit http://91.107.146.137:8000/
3. Click "Sign In"
4. You should be redirected directly to Zitadel (not to the MFE)

## Re-enable MFE Mode Later

If you want to try MFE mode again later (after fixing MFE issues):

```bash
tutor config save --set SSO_USE_MFE=true
tutor config save --set SSO_MFE_URL="http://apps.local.openedx.io:1999"
tutor config save
tutor local restart
```

But first, ensure the MFE is actually running:
```bash
tutor local start -d mfe
tutor local logs -f mfe
```