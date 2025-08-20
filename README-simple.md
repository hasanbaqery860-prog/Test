# Zitadel + Open edX Integration (Simplified)

This is a streamlined setup using Zitadel's native actions for SMS OTP (no separate Node.js server needed) and a Tutor plugin for Open edX integration.

## Quick Start

### 1. Setup Zitadel

```bash
# Run the setup script
./setup-simple.sh

# Or manually:
docker-compose -f docker-compose-simple.yml up -d
```

### 2. Configure Zitadel

1. Access Zitadel Console at `https://auth.yourdomain.com`
2. Create a new Project → "Open edX"
3. Create Application (Web, OIDC)
4. Note the Client ID and Secret

### 3. Add SMS OTP Action

In Zitadel Console:
1. Go to **Actions** → **Create Action**
2. Copy the content from `config/zitadel-sms-otp-kavenegar.js`
3. Update:
   - `KAVENEGAR_API_KEY`
   - `OPENEDX_CLIENT_ID`
4. Add to Login Flow

### 4. Install Tutor Plugin

```bash
# Copy plugin to Tutor
cp zitadel_oauth2.py $(tutor config printroot)/plugins/

# Update the plugin file with your values:
# - ZITADEL_DOMAIN
# - ZITADEL_CLIENT_ID  
# - ZITADEL_CLIENT_SECRET

# Enable plugin
tutor plugins enable zitadel_oauth2
tutor config save
tutor images build openedx mfe
tutor local restart
```

### 5. Configure in Django Admin

1. Access `https://your-openedx.com/admin`
2. Add OAuth2 Provider Config:
   - Backend: `social_core.backends.open_id_connect.OpenIdConnectAuth`
   - Client ID/Secret from Zitadel
   - Enable all checkboxes

## Files Structure

```
├── docker-compose-simple.yml    # Zitadel + PostgreSQL + Nginx
├── zitadel_oauth2.py           # Tutor plugin (copy to Tutor)
├── config/
│   ├── instance-config.yaml    # Zitadel initial setup
│   └── zitadel-sms-otp-kavenegar.js  # SMS OTP action
├── nginx.conf                  # Reverse proxy config
└── setup-simple.sh            # Quick setup script
```

## Testing

1. Basic login: `https://your-openedx.com/login`
2. Direct OAuth: `https://your-openedx.com/auth/login/oidc/?next=/dashboard`

## Troubleshooting

- **No SMS**: Check Kavenegar API key in Zitadel action
- **OAuth error**: Verify redirect URIs and client credentials
- **Action not running**: Check it's added to Login flow

See `zitadel-openedx-simple-guide.md` for detailed instructions.