# Troubleshooting Guide: Authentik + Open edX Integration

## Common Issues and Solutions

### 1. "Unknown command: 'create_oauth2_client'" Error

**Issue:** The command `create_oauth2_client` doesn't exist in Open edX.

**Solution:** Use one of these methods instead:
- **Recommended:** Use the Tutor plugin method (no Django admin needed)
- **Alternative:** Configure through Django Admin UI as described in the guide

### 2. "Sign in with Authentik" Button Not Appearing

**Possible Causes & Solutions:**

a) **Plugin not enabled:**
```bash
# Check if plugin is enabled
tutor plugins list

# Enable if needed
tutor plugins enable authentik_oauth2
tutor config save
```

b) **Services not restarted:**
```bash
tutor local stop
tutor local start -d
```

c) **Images not rebuilt:**
```bash
tutor images build openedx
tutor local restart
```

d) **Feature flags not enabled:**
Check the plugin file contains:
```python
FEATURES["ENABLE_THIRD_PARTY_AUTH"] = True
FEATURES["ENABLE_COMBINED_LOGIN_REGISTRATION"] = True
```

### 3. Redirect URI Mismatch Error

**Error Message:** "The redirect URI provided is missing or does not match"

**Solutions:**

a) **Check exact URLs in Authentik:**
- Must include trailing slashes where appropriate
- Common redirect URIs to add:
  ```
  http://local.openedx.io:8000/auth/complete/oidc/
  http://studio.local.openedx.io:8001/auth/complete/oidc/
  http://local.openedx.io:8000/oauth2/complete/oidc/
  http://studio.local.openedx.io:8001/oauth2/complete/oidc/
  ```

b) **Debug actual redirect URI:**
- Check browser developer tools Network tab
- Look for the `redirect_uri` parameter in the authorization request

### 4. User Creation Fails After Authentication

**Possible Issues:**

a) **Missing email claim:**
- Ensure Authentik is configured to include email scope
- Check property mappings in Authentik

b) **Username conflicts:**
```python
# Add to plugin to handle username conflicts
SOCIAL_AUTH_OIDC_USERNAME_KEY = "preferred_username"
SOCIAL_AUTH_ASSOCIATE_BY_EMAIL = True
```

c) **Check logs:**
```bash
tutor local logs -f lms --tail=100
```

### 5. CORS Errors in Browser Console

**Error:** "Cross-Origin Request Blocked"

**Solution:** Ensure CORS is configured in the plugin:
```python
CORS_ORIGIN_WHITELIST = list(CORS_ORIGIN_WHITELIST) + [
    "http://localhost:9000",
]
```

### 6. "Invalid client" or Authentication Errors

**Check these:**

a) **Client ID and Secret match:**
- In Authentik provider settings
- In Open edX plugin configuration

b) **OIDC endpoint is correct:**
```python
SOCIAL_AUTH_AUTHENTIK_OAUTH2_ENDPOINT = "http://localhost:9000/application/o/openedx/"
```

c) **Test OIDC discovery:**
```bash
curl http://localhost:9000/application/o/openedx/.well-known/openid-configuration
```

### 7. Users Can't Access After Login

**Issue:** Users authenticate but get permission denied

**Solutions:**

a) **In Authentik:**
- Ensure users are in the correct group
- Check application access policies
- Verify the application binding

b) **In Open edX:**
- Check if user was created: Admin → Users
- Verify user is active and staff/superuser if needed

### 8. Debug Mode - Getting More Information

**Enable debug logging:**

1. **In the plugin file:**
```python
SOCIAL_AUTH_OIDC_DEBUG = True
import logging
logging.getLogger('social_core').setLevel(logging.DEBUG)
```

2. **Check logs:**
```bash
# LMS logs
tutor local logs -f lms | grep -i "social\|auth\|oidc"

# All containers
tutor local logs --tail=100
```

### 9. Plugin Changes Not Taking Effect

**Solution sequence:**
```bash
# 1. Save configuration
tutor config save

# 2. Rebuild images (required for plugin changes)
tutor images build openedx

# 3. Restart services
tutor local restart

# 4. Clear Redis cache (if applicable)
tutor local run lms ./manage.py lms cache_programs
```

### 10. Testing the Integration

**Quick test sequence:**

1. **Test Authentik endpoint:**
```bash
curl -I http://localhost:9000/application/o/openedx/.well-known/openid-configuration
```

2. **Test Open edX is running:**
```bash
curl -I http://local.openedx.io:8000/
```

3. **Check feature flags:**
```bash
tutor local run lms ./manage.py lms shell
```
```python
from django.conf import settings
print(settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'))
print(settings.THIRD_PARTY_AUTH_BACKENDS)
```

### 11. Complete Reset (Nuclear Option)

If nothing works, complete reset:

```bash
# 1. Disable plugin
tutor plugins disable authentik_oauth2

# 2. Remove plugin file
rm $(tutor config printroot)/plugins/authentik_oauth2.py

# 3. Save and rebuild
tutor config save
tutor images build openedx

# 4. Start fresh with the setup
```

## Getting Help

When asking for help, provide:
1. Error messages from browser console
2. Logs: `tutor local logs -f lms --tail=200`
3. Your plugin file content (remove secrets)
4. Authentik provider configuration (screenshot)
5. Open edX version: `tutor --version`