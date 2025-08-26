# Quick Fix for Open edX SSO Session Issue

## Problem
Users are redirected to Zitadel for authentication but return unauthorized because session cookies are not being created/maintained when accessing via IP address.

## Root Cause
The session cookie domain is set to `local.openedx.io` but you're accessing via IP address `91.107.146.137`. This prevents the browser from sending session cookies back to the server.

## Solution

### Step 1: Update the SSO Redirect Plugin Configuration

Edit the file `tutor-sso-redirect/tutorssoredirect/plugin.py` and make these changes:

1. **Fix session cookie settings** (around line 130):
```python
# Session and cookie settings for SSO
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 days
SESSION_SAVE_EVERY_REQUEST = True  # Force session save on every request
SESSION_COOKIE_DOMAIN = None  # Set to None to work with IP addresses
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
SESSION_COOKIE_SAMESITE = 'Lax'  # Allow cross-site requests for SSO
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
```

2. **Add enhanced session middleware** (after the imports, around line 160):
```python
class EnhancedSessionMiddleware(SessionMiddleware):
    """Enhanced session middleware that works with IP addresses"""
    
    def process_request(self, request):
        # Call parent method
        super().process_request(request)
        
        # Ensure session is created for IP-based access
        if not hasattr(request, 'session') or not request.session:
            request.session = self.SessionStore()
            request.session.create()
        
        # Set session expiry
        if hasattr(request, 'session') and request.session:
            request.session.set_expiry(settings.SESSION_COOKIE_AGE)
    
    def process_response(self, request, response):
        # Call parent method
        response = super().process_response(request, response)
        
        # Ensure session cookie is set properly for IP access
        if hasattr(request, 'session') and request.session and request.session.modified:
            host = request.get_host()
            if host.replace(':', '').replace('.', '').isdigit():
                # This is an IP address, set cookie without domain restriction
                response.set_cookie(
                    settings.SESSION_COOKIE_NAME,
                    request.session.session_key,
                    max_age=settings.SESSION_COOKIE_AGE,
                    domain=None,  # No domain restriction for IP access
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=settings.SESSION_COOKIE_HTTPONLY,
                    samesite=settings.SESSION_COOKIE_SAMESITE
                )
        
        return response
```

3. **Update middleware configuration** (around line 250):
```python
# Ensure session middleware is properly configured
MIDDLEWARE = [
    'lms.djangoapps.sso_redirect.EnhancedSessionMiddleware',  # Use our enhanced session middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
] + [m for m in MIDDLEWARE if 'SessionMiddleware' not in m and 'EnhancedSessionMiddleware' not in m]
```

4. **Update module creation** (around line 280):
```python
# Create the module
sso_redirect_module = ModuleType('lms.djangoapps.sso_redirect')
sso_redirect_module.SSORedirectMiddleware = SSORedirectMiddleware
sso_redirect_module.EnhancedSessionMiddleware = EnhancedSessionMiddleware

# Add to sys.modules
sys.modules['lms.djangoapps.sso_redirect'] = sso_redirect_module

# Insert middleware at the BEGINNING of the stack
MIDDLEWARE = ['lms.djangoapps.sso_redirect.EnhancedSessionMiddleware', 'lms.djangoapps.sso_redirect.SSORedirectMiddleware'] + MIDDLEWARE
```

### Step 2: Apply the Configuration

If you have access to the Tutor configuration:

```bash
# Set session cookie domain to None
tutor config save --set SESSION_COOKIE_DOMAIN=None
tutor config save --set SESSION_COOKIE_SECURE=False
tutor config save --set SESSION_SAVE_EVERY_REQUEST=True

# Save and restart
tutor config save
tutor local restart
```

### Step 3: Test the Fix

1. Clear your browser cookies for the site
2. Go to http://91.107.146.137:8000/
3. Click "Sign In"
4. Complete authentication with Zitadel
5. You should now be properly logged in and redirected to the dashboard

### Step 4: Verify the Fix

Run the test script to verify the session is working:

```bash
./test_session.sh
```

You should see:
- ✅ Session cookie present
- ✅ Session cookie maintained throughout the flow
- ✅ Dashboard accessible (user authenticated)

## Alternative Solutions

If the above doesn't work, try these alternatives:

### Option 1: Access via Domain Name
Instead of accessing via IP, set up a domain name and access via that:
- Add `91.107.146.137 yourdomain.com` to your hosts file
- Access via `http://yourdomain.com:8000/`

### Option 2: Use HTTPS
If possible, set up HTTPS which often has better cookie handling:
- Set `SESSION_COOKIE_SECURE = True`
- Access via `https://91.107.146.137:8000/`

### Option 3: Browser-Specific Fix
Some browsers have stricter cookie policies. Try:
- Using Chrome in incognito mode
- Disabling third-party cookie blocking
- Adding the site to trusted sites

## Debugging

If the issue persists, check the logs:

```bash
# Check session-related logs
tutor local logs -f lms | grep -E "(session|cookie|auth)"

# Check if users are being created
tutor local exec lms ./manage.py lms shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.count()
```

## Expected Behavior After Fix

1. Session cookies should be created with no domain restriction
2. Users should remain logged in after Zitadel authentication
3. The dashboard should be accessible without re-authentication
4. Session cookies should persist across browser sessions