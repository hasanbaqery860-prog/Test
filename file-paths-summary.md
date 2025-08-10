# File Paths Summary for Authentik + Open edX Integration

## Files Created/Modified in Open edX

### 1. Tutor Plugin File (Main Configuration)
**Path:** `$(tutor config printroot)/plugins/authentik_oauth2.py`
- Usually located at: `~/.local/share/tutor/plugins/authentik_oauth2.py`
- This is the ONLY file you need to create/modify
- Contains all OAuth2 configuration for both LMS and CMS

### 2. No Core Open edX Files Modified
The beauty of using Tutor plugins is that you don't need to modify any core Open edX files. The plugin system injects the configuration into:
- `lms/envs/common.py` (via openedx-lms-common-settings patch)
- `cms/envs/common.py` (via openedx-cms-common-settings patch)

## Configuration Locations in Open edX

### Django Admin Configuration (Alternative Method)
- URL: `http://local.openedx.io:8000/admin`
- Navigate to: **Third Party Auth** → **Provider Configuration**
- This is stored in the database, not in files

### Site Configuration
- Stored in database via Django admin
- URL: `http://local.openedx.io:8000/admin/site_configuration/siteconfiguration/`

## Key Open edX Directories (For Reference)

### In Docker Containers
- LMS settings: `/openedx/edx-platform/lms/envs/`
- CMS settings: `/openedx/edx-platform/cms/envs/`
- Third-party auth app: `/openedx/edx-platform/common/djangoapps/third_party_auth/`

### On Host System (Tutor)
- Tutor root: `$(tutor config printroot)` (usually `~/.local/share/tutor/`)
- Tutor config: `$(tutor config printroot)/config.yml`
- Plugins directory: `$(tutor config printroot)/plugins/`
- Environment files: `$(tutor config printroot)/env/`

## Important URLs

### Open edX URLs
- LMS: `http://local.openedx.io:8000/`
- Studio: `http://studio.local.openedx.io:8001/`
- Django Admin: `http://local.openedx.io:8000/admin`

### OAuth2 Callback URLs
- LMS: `http://local.openedx.io:8000/auth/complete/oidc/`
- Studio: `http://studio.local.openedx.io:8001/auth/complete/oidc/`

### Authentik URLs
- Main panel: `http://localhost:9000/`
- OIDC Discovery: `http://localhost:9000/application/o/openedx/.well-known/openid-configuration`
- Authorization: `http://localhost:9000/application/o/authorize/`
- Token: `http://localhost:9000/application/o/token/`
- UserInfo: `http://localhost:9000/application/o/userinfo/`

## Commands Summary

### Setup Commands
```bash
# Create plugin directory
mkdir -p $(tutor config printroot)/plugins

# Copy plugin file
cp authentik_oauth2.py $(tutor config printroot)/plugins/

# Enable plugin
tutor plugins enable authentik_oauth2

# Save configuration
tutor config save

# Rebuild images (required after plugin changes)
tutor images build openedx

# Restart services
tutor local stop
tutor local start -d
```

### Verification Commands
```bash
# Check if plugin is enabled
tutor plugins list

# View current configuration
tutor config printvalue FEATURES

# Access Django shell
tutor local run lms ./manage.py lms shell

# Create superuser
tutor local run lms ./manage.py lms createsuperuser
```

## Troubleshooting File Locations

### Log Files
- LMS logs: `tutor local logs -f lms`
- CMS logs: `tutor local logs -f cms`

### Debug Configuration
Add to plugin file for debugging:
```python
SOCIAL_AUTH_OIDC_DEBUG = True
LOGGING['handlers']['console']['level'] = 'DEBUG'
```

## Summary
The integration requires creating only ONE file:
- `$(tutor config printroot)/plugins/authentik_oauth2.py`

Everything else is configured through:
1. Authentik web panel
2. Django admin interface (optional)
3. Tutor commands

No core Open edX files need to be modified, making this integration clean and maintainable.