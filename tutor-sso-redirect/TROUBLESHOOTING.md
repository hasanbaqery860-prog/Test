# Troubleshooting Zitadel Authentication Issues

## Common Issue: User Not Logged In After Zitadel Redirect

If users are being redirected back from Zitadel but remain signed out, follow these steps:

## 1. Quick Fix - Run Configuration Script

```bash
# Inside your tutor environment, run:
tutor local exec lms python /openedx/configure_oidc_provider.py

# Then restart LMS:
tutor local restart lms
```

## 2. Verify OIDC Provider Configuration

Run the debug script to check your configuration:

```bash
tutor local exec lms python /openedx/debug_auth_flow.py
```

Look for these critical items:
- ✅ OAuth2 Provider Configuration exists in database
- ✅ OIDC provider is enabled
- ✅ Client ID and Secret are set
- ✅ Third party auth is enabled

## 3. Manual Configuration Check

Access Django admin:
1. Go to: http://91.107.146.137:8000/admin/
2. Login with your superuser credentials
3. Navigate to: **Third Party Auth** → **OAuth2 Provider Configs**
4. Ensure you have an OIDC provider with:
   - **Enabled**: ✓
   - **Name**: `oidc`
   - **Slug**: `oidc`
   - **Backend name**: `social_core.backends.open_id_connect.OpenIdConnectAuth`
   - **Skip registration form**: ✓
   - **Skip email verification**: ✓

## 4. Check Zitadel Configuration

Ensure your Zitadel application has:

### Redirect URLs:
```
http://91.107.146.137:8000/auth/complete/oidc/
```

### Grant Types:
- Authorization Code
- Refresh Token

### Scopes:
- openid
- profile
- email

## 5. Clear Browser Data

1. Clear all cookies for your domain
2. Clear browser cache
3. Try incognito/private browsing mode

## 6. Monitor Logs During Login

```bash
# In one terminal, watch the logs:
tutor local logs -f lms | grep -E "SSO|social|oauth|oidc|session"

# In another terminal, attempt to login
```

## 7. Check Session Cookie

In browser developer tools (F12):
1. Go to Application/Storage → Cookies
2. After login attempt, look for `sessionid` cookie
3. If missing, session is not being created

## 8. Advanced Debugging

### Check if user was created:
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

### Check sessions:
```bash
tutor local exec lms ./manage.py lms shell
>>> from django.contrib.sessions.models import Session
>>> from datetime import datetime
>>> Session.objects.filter(expire_date__gte=datetime.now()).count()
# Should show active sessions
```

## 9. Force Rebuild

If nothing else works:
```bash
# Rebuild the image with the latest changes
tutor images build openedx

# Stop and start services
tutor local stop
tutor local start -d
```

## 10. Common Error Messages

### "Can't fetch setting of a disabled backend/provider"
- OIDC provider is not configured in Django admin
- Run: `tutor local exec lms python /openedx/configure_oidc_provider.py`

### "Authentication process canceled"
- Check Zitadel redirect URLs match exactly
- Ensure client ID includes @projectname suffix

### Session not persisting
- Browser blocking third-party cookies
- SESSION_COOKIE_DOMAIN mismatch
- Missing session middleware

## Still Having Issues?

1. Check that your tutor configuration has the correct values:
```bash
tutor config printvalue SSO_OIDC_KEY
tutor config printvalue SSO_OIDC_SECRET
tutor config printvalue SSO_OIDC_ENDPOINT
```

2. Ensure these are set correctly for your Zitadel instance

3. Try the test script:
```bash
cd /workspace/tutor-sso-redirect
python test_oidc_auth.py http://91.107.146.137:8000
```

4. Check for JavaScript errors in browser console during login

5. Verify network requests in browser developer tools:
   - Check the `/auth/login/oidc/` redirect
   - Check the `/auth/complete/oidc/` callback
   - Look for any 4xx or 5xx errors