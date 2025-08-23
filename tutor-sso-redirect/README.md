# Tutor SSO Redirect Plugin

This Tutor plugin disables the default Open edX login and registration pages and redirects all authentication requests to your pre-configured SSO endpoint.

## Features

- Completely disables native Open edX login and registration
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
2. **Middleware interception**: Injects a middleware directly into the settings that intercepts all requests to login/register URLs
3. **URL overrides**: Overrides the default URL patterns to redirect to SSO
4. **Feature flags**: Disables various authentication-related features in Open edX

### URLs That Get Redirected

- `/login`
- `/register`
- `/signin`
- `/signup`
- `/user_api/v1/account/login_session/`
- `/api/user/v1/account/login_session/`
- `/user_api/v2/account/login_session/`
- `/api/user/v2/account/login_session/`

### URLs That Remain Accessible

- `/auth/*` (all third-party auth URLs)
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

### Users Still See Login Page

1. Ensure the plugin is enabled: `tutor plugins list`
2. Verify configuration was saved: `tutor config save`
3. Restart services: `tutor local restart`
4. Clear browser cache

### Redirect Loops

If you experience redirect loops:
1. Ensure your SSO is properly configured
2. Check that the `/auth/*` URLs are accessible
3. Verify the `LOGIN_REDIRECT_URL` setting

### Testing Redirects

```bash
# Test a specific URL
curl -I https://your-lms-domain/login

# Should return:
# HTTP/1.1 302 Found
# Location: /auth/login/oidc/
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