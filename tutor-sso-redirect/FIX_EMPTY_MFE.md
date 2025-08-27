# Fix for Empty MFE Page Issue

The issue you're experiencing (empty page at http://apps.local.openedx.io:1999/login) indicates that either:
1. The MFE is not running properly
2. The MFE is not configured correctly
3. There's a URL routing issue

## Immediate Solution: Use Direct SSO Mode

Since the MFE is not working, let's bypass it completely:

```bash
# 1. Disable MFE mode
tutor config save --set SSO_USE_MFE=false

# 2. Save and restart
tutor config save
tutor local restart

# 3. Clear browser cookies and try again
```

Now when you click "Sign In", you'll go directly to Zitadel instead of the MFE.

## Alternative: Fix the MFE

If you want to use the MFE, here's how to fix it:

### 1. Check if MFE is running
```bash
tutor local status | grep mfe
# or
docker ps | grep mfe
```

### 2. If MFE is not running, start it
```bash
tutor local start -d mfe
```

### 3. Check MFE logs for errors
```bash
tutor local logs -f mfe
```

### 4. Rebuild MFE if needed
```bash
tutor images build mfe
tutor local restart mfe
```

### 5. Check your hosts file
Ensure `/etc/hosts` (Linux/Mac) or `C:\Windows\System32\drivers\etc\hosts` (Windows) contains:
```
127.0.0.1 apps.local.openedx.io
```

### 6. Access MFE directly
Try accessing: http://apps.local.openedx.io:1999/learning
If this works, the MFE is running but the authn app might have issues.

## Why This Happens

The Open edX platform is trying to use the MFE for authentication, but:
- The MFE authn app might not be built/included
- The MFE container might not be running
- There might be a configuration mismatch

## Recommended Approach

For now, use Direct SSO mode (SSO_USE_MFE=false) which:
- Is simpler and more reliable
- Bypasses potential MFE issues
- Still provides full SSO functionality with Zitadel

Once everything is working with direct mode, you can troubleshoot the MFE separately if needed.