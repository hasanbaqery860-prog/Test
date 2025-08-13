# Quick Workaround: Use Legacy Login Page

If you want to test Authentik login immediately without rebuilding MFE, you can use the legacy login page:

## Option 1: Direct Legacy Login URL
Visit: `http://local.openedx.io:8000/login`
(Note: NOT `/authn/login` which is the MFE)

## Option 2: Temporarily Disable MFE Login
Add this to your plugin to redirect to legacy login:

```python
# Add this to authentik_oauth2.py
hooks.Filters.ENV_PATCHES.add_item(
    (
        "openedx-lms-common-settings",
        """
# Temporarily use legacy login instead of MFE
ENABLE_AUTHN_MICROFRONTEND = False
"""
    )
)
```

Then:
```bash
tutor config save
tutor local restart openedx
```

## Option 3: Direct OAuth2 Login Link
You can also directly visit:
`http://local.openedx.io:8000/auth/login/oidc/?auth_entry=login&next=/dashboard`

This will start the Authentik authentication flow directly.