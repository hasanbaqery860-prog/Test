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
   - **Send welcome email**: ☐ (unchecked)
   - **Visible**: ✓ (checked)
   - **Enable sso id verification**: ☐ (unchecked)
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

## 4. Configure Zitadel Application

In your Zitadel application:

### Application Settings:
1. **Application Type**: Web Application
2. **Authentication Method**: Code
3. **Grant Types**: Authorization Code, Refresh Token

### Redirect URLs:
Add ALL of these:
```
http://localhost:8000/auth/complete/oidc/
http://localhost:8001/auth/complete/oidc/
http://91.107.146.137:8000/auth/complete/oidc/
http://91.107.146.137:8001/auth/complete/oidc/
http://apps.local.openedx.io:1999/auth/complete/oidc/
https://your-domain.com/auth/complete/oidc/
```

### Post Logout Redirect URLs:
```
http://localhost:8000/
http://localhost:8001/
http://91.107.146.137:8000/
http://91.107.146.137:8001/
https://your-domain.com/
```

### Token Settings:
- **Auth Token Type**: JWT
- **Access Token Type**: JWT
- **ID Token Userinfo**: ✓ (Add userinfo inside ID token)

### Scopes:
Ensure these scopes are enabled:
- `openid`
- `profile`
- `email`

## 5. Restart Services

```bash
tutor local restart
```

## 6. Test Authentication

1. Go to http://localhost:8000/login
2. You should be redirected to Zitadel
3. Login with your Zitadel credentials
4. You should be redirected back to Open edX dashboard

## 7. Debug Authentication Issues

If the user is not being logged in after returning from Zitadel:

```bash
# Check authentication debug info
tutor local exec lms python /openedx/debug_auth.py

# Check logs during login attempt
tutor local logs -f lms | grep -E "(social|third_party_auth|SSO)"

# Check if user was created
tutor local exec lms ./manage.py lms shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(email='your-email@example.com').exists()
```

## Common Issues

### "Can't fetch setting of a disabled backend/provider"
- The OIDC provider isn't configured in Django admin (see step 3)

### User not logged in after Zitadel redirect
- Check that "Skip registration form" is checked in Django admin
- Ensure `SOCIAL_AUTH_AUTO_CREATE_USERS = True` in settings
- Check Zitadel is returning proper user info (email, name)

### "Invalid client" error from Zitadel
- Client ID must include @projectname suffix
- Client secret must match exactly
- Redirect URLs must be exact match (including protocol and port)

### Session not persisting
- Clear browser cookies
- Check SESSION_COOKIE_DOMAIN is appropriate for your setup
- Ensure cookies are not blocked by browser

## Testing User Creation

After successful Zitadel login, check if user was created:

```bash
tutor local exec lms ./manage.py lms shell
>>> from social_django.models import UserSocialAuth
>>> UserSocialAuth.objects.all()
# Should show your SSO users

>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(email='your-email@example.com')
# Should show the created user
```