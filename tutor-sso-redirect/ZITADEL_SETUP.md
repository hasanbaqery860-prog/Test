# Zitadel OIDC Setup for Open edX

## 1. Get Your Zitadel Configuration

From your Zitadel application, you need:

1. **Client ID** (e.g., `123456789@projectname`)
2. **Client Secret** (generate one if you haven't)
3. **OIDC Discovery Endpoint** (e.g., `https://your-zitadel-instance.zitadel.cloud`)

## 2. Configure the Plugin

Set these values in your Tutor configuration:

```bash
# Set your Zitadel client credentials
tutor config save --set SSO_OIDC_KEY="your-client-id@projectname"
tutor config save --set SSO_OIDC_SECRET="your-client-secret"
tutor config save --set SSO_OIDC_ENDPOINT="https://your-zitadel-instance.zitadel.cloud"

# Save the configuration
tutor config save
```

## 3. Configure OAuth2 Provider in Django Admin

After restarting, you need to enable the OIDC provider in Django admin:

```bash
# Create a superuser if you don't have one
tutor local exec lms ./manage.py lms createsuperuser

# Access Django admin
# Go to: http://localhost:8000/admin
```

In Django Admin:

1. Navigate to **Third Party Auth** → **OAuth2 Provider Configs**
2. Click **Add OAuth2 Provider Config**
3. Fill in:
   - **Enabled**: ✓ (checked)
   - **Name**: `oidc` (MUST be exactly 'oidc')
   - **Slug**: `oidc` (MUST be exactly 'oidc')
   - **Site**: Select your site
   - **Skip registration form**: ✓ (checked)
   - **Skip email verification**: ✓ (checked)
   - **Backend name**: `social_core.backends.open_id_connect.OpenIdConnectAuth`
   - **Client ID**: (same as SSO_OIDC_KEY)
   - **Client Secret**: (same as SSO_OIDC_SECRET)
   - **Other settings**:
     ```json
     {
       "OIDC_ENDPOINT": "https://your-zitadel-instance.zitadel.cloud"
     }
     ```

4. Click **Save**

## 4. Add Redirect URLs in Zitadel

In your Zitadel application settings, add these redirect URLs:

```
http://localhost:8000/auth/complete/oidc/
http://localhost:8001/auth/complete/oidc/
http://91.107.146.137:8000/auth/complete/oidc/
http://91.107.146.137:8001/auth/complete/oidc/
http://apps.local.openedx.io:1999/auth/complete/oidc/
```

Also add post-logout redirect URLs:
```
http://localhost:8000/
http://localhost:8001/
http://91.107.146.137:8000/
http://91.107.146.137:8001/
```

## 5. Restart Services

```bash
tutor local restart
```

## 6. Test It

1. Go to http://localhost:8000/login
2. You should be redirected to Zitadel
3. Login with your Zitadel credentials
4. You should be redirected back to Open edX dashboard

## Troubleshooting

### "Can't fetch setting of a disabled backend/provider"

This means the OIDC provider isn't configured in Django admin. Follow step 3 above.

### "Invalid client" error from Zitadel

Check that:
- Client ID matches exactly (including @projectname suffix)
- Client secret is correct
- Redirect URLs are added in Zitadel

### Still redirecting to MFE

Clear your browser cache and cookies, then try again.

### Check if OIDC is enabled

```bash
tutor local exec lms python -c "from django.conf import settings; print('OIDC enabled:', settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH', False))"
```