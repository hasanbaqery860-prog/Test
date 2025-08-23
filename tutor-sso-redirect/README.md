# Tutor SSO Redirect Plugin

This Tutor plugin disables the default Open edX login and registration pages and redirects all authentication requests to an SSO provider using OpenID Connect (OIDC).

## Features

- Completely disables native Open edX login and registration
- Redirects all authentication requests to `/auth/login/oidc/`
- Configurable SSO endpoint
- Preserves "next" URL parameter for post-login redirection
- Disables password reset functionality
- Works with both LMS and CMS (Studio)
- Compatible with Open edX Teak release

## Requirements

- Tutor >= 18.0.0
- Open edX Teak release or later
- An SSO provider that supports OpenID Connect (e.g., Azure AD, Keycloak, Auth0)

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

4. Rebuild the Open edX images to include the middleware:

```bash
tutor images build openedx
```

5. Restart your platform:

```bash
tutor local launch
```

## Configuration

### Basic Configuration

The plugin provides several configuration options that can be set using `tutor config`:

```bash
# Enable/disable the SSO redirect (default: true)
tutor config save --set SSO_REDIRECT_ENABLED=true

# Set the SSO endpoint (default: /auth/login/oidc/)
tutor config save --set SSO_OIDC_ENDPOINT="/auth/login/oidc/"

# Set the SSO provider name (default: azuread-oauth2)
tutor config save --set SSO_PROVIDER_NAME="azuread-oauth2"
```

### Configuring Your SSO Provider

You'll need to configure your SSO provider in the Django admin:

1. Access the Django admin at `https://your-lms-domain/admin`
2. Navigate to **Third Party Auth** → **OAuth2 Provider Config**
3. Add a new provider configuration with your SSO details:
   - **Provider**: Choose your provider type
   - **Name**: A display name for the provider
   - **Client ID**: Your OAuth2 client ID
   - **Client Secret**: Your OAuth2 client secret
   - **Other settings**: Configure according to your provider's requirements

### Azure AD Example Configuration

For Azure AD, you would typically configure:

- **Provider**: `azuread-oauth2`
- **Name**: `Azure AD`
- **Client ID**: Your Azure application ID
- **Client Secret**: Your Azure application secret
- **Other settings**:
  ```json
  {
    "tenant": "your-tenant-id"
  }
  ```

## How It Works

The plugin works by:

1. **Disabling native authentication**: Sets Django settings to disable registration and login features
2. **Middleware interception**: Installs a middleware that intercepts all requests to login/register URLs
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

## Customization

### Modifying Redirect URLs

To add or remove URLs from the redirect list, edit the `AUTH_URLS` list in `/tutorssoredirect/openedx/tutorssoredirect/middleware.py`:

```python
AUTH_URLS = [
    '/login',
    '/register',
    # Add your custom URLs here
]
```

### Changing the SSO Provider

To use a different SSO provider (e.g., Google, GitHub), update the `AUTHENTICATION_BACKENDS` in the plugin patches and ensure the corresponding social auth backend is installed.

## Troubleshooting

### Users Still See Login Page

1. Ensure the plugin is enabled: `tutor plugins list`
2. Check that images were rebuilt: `tutor images build openedx`
3. Verify middleware is loaded: Check LMS logs for middleware initialization

### SSO Login Fails

1. Verify your SSO provider configuration in Django admin
2. Check that the callback URL is correctly configured in your SSO provider
3. Review LMS logs for authentication errors

### Redirect Loops

If you experience redirect loops:
1. Ensure your SSO provider is properly configured
2. Check that the `/auth/*` URLs are accessible
3. Verify the `LOGIN_REDIRECT_URL` setting

## Development

To contribute to this plugin:

1. Clone the repository
2. Install in development mode: `pip install -e .`
3. Make your changes
4. Test with: `tutor local launch`

## License

This plugin is licensed under the AGPLv3 license.

## Support

For issues and feature requests, please use the GitHub issue tracker.