# Debugging Authentik Integration with Open edX

Follow these steps to debug why the Authentik login button is not appearing:

## Step 1: Verify Plugin is Enabled

```bash
# Check if the plugin is enabled
tutor plugins list

# If not enabled, enable it:
tutor plugins enable authentik_oauth2

# Rebuild the Open edX images after enabling
tutor images build openedx
```

## Step 2: Check Plugin File Location

```bash
# Verify the plugin file is in the correct location
ls -la $(tutor config printroot)/plugins/authentik_oauth2.py

# Check if the file has proper permissions
cat $(tutor config printroot)/plugins/authentik_oauth2.py
```

## Step 3: Verify Configuration Applied

```bash
# Save the configuration to apply patches
tutor config save

# Check if patches were applied
tutor config printvalue OPENEDX_LMS_COMMON_SETTINGS | grep -i authentik
tutor config printvalue OPENEDX_LMS_COMMON_SETTINGS | grep -i "THIRD_PARTY_AUTH"
```

## Step 4: Restart Services

```bash
# Restart all services to apply changes
tutor local stop
tutor local start -d

# Or just restart LMS
tutor local restart openedx
```

## Step 5: Check LMS Settings Inside Container

```bash
# Enter the LMS container
tutor local exec lms bash

# Inside the container, check Django settings
python manage.py lms shell
```

Then in the Python shell:
```python
from django.conf import settings

# Check if third party auth is enabled
print("FEATURES['ENABLE_THIRD_PARTY_AUTH']:", settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'))

# Check authentication backends
print("\nAUTHENTICATION_BACKENDS:")
for backend in settings.AUTHENTICATION_BACKENDS:
    print(f"  - {backend}")

# Check third party auth backends
print("\nTHIRD_PARTY_AUTH_BACKENDS:", getattr(settings, 'THIRD_PARTY_AUTH_BACKENDS', 'Not set'))

# Check OAuth2 settings
print("\nOAuth2 Settings:")
print(f"  SOCIAL_AUTH_OIDC_KEY: {getattr(settings, 'SOCIAL_AUTH_OIDC_KEY', 'Not set')}")
print(f"  SOCIAL_AUTH_OIDC_SECRET: {'*****' if hasattr(settings, 'SOCIAL_AUTH_OIDC_SECRET') else 'Not set'}")
print(f"  SOCIAL_AUTH_OIDC_OIDC_ENDPOINT: {getattr(settings, 'SOCIAL_AUTH_OIDC_OIDC_ENDPOINT', 'Not set')}")

# Exit Python shell
exit()
```

## Step 6: Configure OAuth2 Provider in Django Admin

```bash
# Create a superuser if you haven't already
tutor local exec lms python manage.py lms createsuperuser
```

1. Access Django admin: `http://your-lms-domain/admin`
2. Navigate to **Third Party Auth → OAuth2 Provider Config**
3. Add a new provider with these settings:
   - **Enabled**: ✓ (checked)
   - **Skip registration form**: ✓ (optional)
   - **Skip email verification**: ✓ (optional)
   - **Name**: `oidc` (MUST be exactly this)
   - **Slug**: `oidc` (MUST be exactly this)
   - **Site**: Select your site
   - **Backend name**: `social_core.backends.open_id_connect.OpenIdConnectAuth`
   - **Client ID**: Your Authentik client ID
   - **Client Secret**: Your Authentik client secret
   - **Other settings**: Can be left empty

## Step 7: Check Database Configuration

```bash
# Enter MySQL to check the configuration
tutor local exec mysql mysql -u root -p$(tutor config printvalue MYSQL_ROOT_PASSWORD)
```

In MySQL:
```sql
USE openedx;

-- Check if third party auth provider exists
SELECT * FROM third_party_auth_oauth2providerconfig WHERE backend_name LIKE '%open_id_connect%';

-- Check if it's enabled
SELECT name, enabled, backend_name FROM third_party_auth_oauth2providerconfig;

-- Exit MySQL
EXIT;
```

## Step 8: Debug Login Page Rendering

```bash
# Check LMS logs for errors
tutor local logs -f lms | grep -i "auth\|error\|third"

# In another terminal, visit the login page and watch for errors
# Visit: http://your-lms-domain/login
```

## Step 9: Check Browser Console

1. Open browser developer tools (F12)
2. Go to Console tab
3. Visit the login page
4. Look for JavaScript errors

## Step 10: Verify Login Page Template

```bash
# Check if the login page is loading third party auth
tutor local exec lms bash -c "grep -r 'third-party-auth' /openedx/edx-platform/lms/templates/"
```

## Step 11: Force Clear Cache

```bash
# Clear Django cache
tutor local exec lms python manage.py lms shell -c "from django.core.cache import cache; cache.clear()"

# Restart memcached
tutor local restart memcached
```

## Step 12: Test with Debug Mode

Add this to your plugin temporarily for debugging:
```python
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# Debug mode for OAuth2
SOCIAL_AUTH_OIDC_DEBUG = True
import logging
logging.basicConfig(level=logging.DEBUG)
"""
    )
)
```

Then:
```bash
tutor config save
tutor local restart openedx
```

## Common Issues and Solutions

### Issue 1: Provider Not Configured
**Solution**: Make sure you've added the OAuth2 provider in Django admin (Step 6)

### Issue 2: Wrong Backend Name
**Solution**: The slug MUST be `oidc` to match the backend name

### Issue 3: Site Configuration
**Solution**: Make sure the provider is associated with the correct site in Django admin

### Issue 4: Cache Issues
**Solution**: Clear all caches and restart services

### Issue 5: Feature Flag Not Enabled
**Solution**: Verify `FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True` is set

## Verification Commands Summary

Run these commands to get a full diagnostic:
```bash
# 1. Check plugin
tutor plugins list | grep authentik

# 2. Check configuration
tutor config printvalue OPENEDX_LMS_COMMON_SETTINGS | grep -A5 -B5 "THIRD_PARTY_AUTH"

# 3. Check logs
tutor local logs lms | grep -i "third.*party\|oauth\|oidc" | tail -20

# 4. Inside LMS container
tutor local exec lms python manage.py lms shell -c "
from django.conf import settings
print('Third Party Auth Enabled:', settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'))
print('OAuth2 Backends:', getattr(settings, 'THIRD_PARTY_AUTH_BACKENDS', []))
"
```

## Report Back

After going through these steps, please report:
1. Which step showed an issue?
2. What error messages did you see?
3. What's the output of the verification commands?

This will help identify exactly where the integration is failing.