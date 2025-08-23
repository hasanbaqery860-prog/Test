# Tutor SSO Redirect Plugin

This Tutor plugin disables the default Open edX login and registration pages and redirects all authentication requests to your pre-configured SSO endpoint.

## Features

- Completely disables native Open edX login and registration
- Disables the authn MFE (Micro Frontend)
- Redirects all authentication requests to your SSO endpoint
- Preserves "next" URL parameter for post-login redirection
- Disables password reset functionality
- Works with both LMS and CMS (Studio)
- Compatible with Open edX Teak release

## Requirements

- Tutor >= 18.0.0
- Open edX Teak release or later
- Pre-configured SSO authentication (e.g., Auth0, Azure AD, Keycloak)

## Installation

1. Install the plugin:

```bash
pip install -e /path/to/tutor-sso-redirect
```

Or install from GitHub:

```bash
pip install git+https://github.com/yourusername/tutor-sso-redirect.git
```

2. Enable the plugin:

```bash
tutor plugins enable sso-redirect
```

3. Save the configuration:

```bash
tutor config save
```

4. Restart your platform (no image rebuild needed):

```bash
tutor local restart
```

## Configuration

The plugin provides two configuration options:

```bash
# Enable/disable the SSO redirect (default: true)
tutor config save --set SSO_REDIRECT_ENABLED=true

# Set the SSO redirect URL (default: /auth/login/oidc/)
tutor config save --set SSO_REDIRECT_URL="/auth/login/oidc/"
```

If your SSO is configured at a different URL, update `SSO_REDIRECT_URL` accordingly.

## How It Works

The plugin works by:

1. **Disabling native authentication**: Sets Django settings to disable registration and login features
2. **Disabling authn MFE**: Prevents the authentication micro-frontend from loading
3. **Middleware interception**: Injects a middleware directly into the settings that intercepts all requests to login/register URLs
4. **URL overrides**: Overrides the default URL patterns to redirect to SSO
5. **Feature flags**: Disables various authentication-related features in Open edX

### URLs That Get Redirected

- `/login`, `/register`, `/signin`, `/signup`
- `/authn/login`, `/authn/register`, `/authn/logistration` (MFE URLs)
- `/auth/login`, `/create_account`
- `/user_api/v1/account/login_session/`
- `/api/user/v1/account/login_session/`
- `/user_api/v2/account/login_session/`
- `/api/user/v2/account/login_session/`
- Any URL containing login/register/signin/signup patterns

### URLs That Remain Accessible

- `/auth/login/oidc/` (or your configured SSO URL)
- `/auth/complete/*` (OAuth completion URLs)
- `/logout`
- `/admin/*`
- `/api/*` (except login endpoints)
- Static and media files
- Health check endpoints

## Testing

Use the included test script to verify the redirects are working:

```bash
python test_redirect.py https://your-lms-domain

# Expected output:
# ✓ /login -> /auth/login/oidc/
# ✓ /register -> /auth/login/oidc/
# ✓ /signin -> /auth/login/oidc/
# ✓ /signup -> /auth/login/oidc/
# ✓ /authn/login -> /auth/login/oidc/
# ✓ /authn/register -> /auth/login/oidc/
```

## Customization

### Changing the SSO Redirect URL

If your SSO endpoint is different from `/auth/login/oidc/`, update it using:

```bash
tutor config save --set SSO_REDIRECT_URL="/your/sso/endpoint/"
tutor config save
tutor local restart
```

### Modifying Redirect URLs

To add or remove URLs from the redirect list, you'll need to modify the `AUTH_URLS` list in the plugin.py file in the middleware definition.

## Troubleshooting

### Authn MFE Still Accessible

If you can still access `http://apps.local.openedx.io:1999/authn/login`:

1. Clear your browser cache
2. Ensure the plugin is properly installed and enabled
3. Check that the configuration was saved: `tutor config save`
4. Restart all services: `tutor local restart`
5. If using Tutor dev mode: `tutor dev restart`

### Users Still See Login Page

1. Ensure the plugin is enabled: `tutor plugins list`
2. Verify configuration was saved: `tutor config save`
3. Restart services: `tutor local restart`
4. Clear browser cache
5. Check that your SSO endpoint is working

### Direct IP Access

If accessing via IP address (e.g., `91.107.146.137:8000`), the redirect should still work. If not:
1. Check that the plugin is enabled on that instance
2. Ensure the SSO_REDIRECT_URL is accessible from that IP

### Redirect Loops

If you experience redirect loops:
1. Ensure your SSO is properly configured
2. Check that the SSO endpoint URL is in the ALLOWED_URLS list
3. Verify the `LOGIN_REDIRECT_URL` setting

### Testing Redirects

```bash
# Test a specific URL
curl -I https://your-lms-domain/login

# Should return:
# HTTP/1.1 302 Found
# Location: /auth/login/oidc/

# Test authn MFE URL
curl -I https://your-lms-domain/authn/login

# Should also redirect
```

### Checking Logs

```bash
# Check LMS logs for any errors
tutor local logs -f lms

# Look for middleware initialization
tutor local logs lms | grep SSORedirectMiddleware
```

## Development

To contribute to this plugin:

1. Clone the repository
2. Install in development mode: `pip install -e .`
3. Make your changes
4. Test with: `tutor local restart`

## License

This plugin is licensed under the AGPLv3 license.

## Support

For issues and feature requests, please use the GitHub issue tracker.