# Zitadel Self-Hosted Setup with Open edX Integration and SMS OTP

This guide provides step-by-step instructions for setting up a self-hosted Zitadel instance using Docker Compose, integrating it with Open edX for authentication, and implementing SMS OTP functionality using Kavenegar.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setting Up Zitadel with Docker Compose](#setting-up-zitadel-with-docker-compose)
3. [Configuring Zitadel](#configuring-zitadel)
4. [Integrating Zitadel with Open edX](#integrating-zitadel-with-open-edx)
5. [Adding SMS OTP with Kavenegar](#adding-sms-otp-with-kavenegar)
6. [Troubleshooting](#troubleshooting)
7. [Security Considerations](#security-considerations)

## Prerequisites

Before starting, ensure you have:

- Docker and Docker Compose installed (version 20.10+ and 1.29+ respectively)
- A domain name with SSL certificates (Let's Encrypt recommended)
- Open edX instance (Lilac release or later)
- Kavenegar account with API key
- Basic knowledge of Docker, OAuth2/OIDC, and Open edX configuration

## Setting Up Zitadel with Docker Compose

### 1. Create Directory Structure

```bash
mkdir -p zitadel-setup/{config,certs,data}
cd zitadel-setup
```

### 2. Create Docker Compose Configuration

Create a `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  zitadel:
    image: ghcr.io/zitadel/zitadel:latest
    command: 'start-from-init --masterkeyFromEnv --tlsMode disabled'
    environment:
      - ZITADEL_EXTERNALPORT=8080
      - ZITADEL_EXTERNALDOMAIN=auth.yourdomain.com
      - ZITADEL_EXTERNALSECURE=true
      - ZITADEL_TLS_ENABLED=false
      - ZITADEL_MASTERKEY=${ZITADEL_MASTERKEY}
      - ZITADEL_DATABASE_POSTGRES_HOST=postgres
      - ZITADEL_DATABASE_POSTGRES_PORT=5432
      - ZITADEL_DATABASE_POSTGRES_DATABASE=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_USERNAME=zitadel
      - ZITADEL_DATABASE_POSTGRES_USER_PASSWORD=${POSTGRES_PASSWORD}
      - ZITADEL_DATABASE_POSTGRES_USER_SSL_MODE=disable
      - ZITADEL_DATABASE_POSTGRES_ADMIN_USERNAME=postgres
      - ZITADEL_DATABASE_POSTGRES_ADMIN_PASSWORD=${POSTGRES_PASSWORD}
      - ZITADEL_DATABASE_POSTGRES_ADMIN_SSL_MODE=disable
      - ZITADEL_FIRSTINSTANCE_PATPATH=/app/config/instance-config.yaml
      - ZITADEL_DEFAULTINSTANCE_SMTPCONFIGURATION_SMTP_HOST=${SMTP_HOST}
      - ZITADEL_DEFAULTINSTANCE_SMTPCONFIGURATION_SMTP_USER=${SMTP_USER}
      - ZITADEL_DEFAULTINSTANCE_SMTPCONFIGURATION_SMTP_PASSWORD=${SMTP_PASSWORD}
      - ZITADEL_DEFAULTINSTANCE_SMTPCONFIGURATION_FROM=${SMTP_FROM}
    ports:
      - '8080:8080'
    depends_on:
      postgres:
        condition: service_healthy
    volumes:
      - ./config/instance-config.yaml:/app/config/instance-config.yaml:ro
      - zitadel-certs:/app/certs
    networks:
      - zitadel-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=zitadel
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - zitadel-network

  nginx:
    image: nginx:alpine
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - zitadel
    networks:
      - zitadel-network

volumes:
  postgres-data:
  zitadel-certs:

networks:
  zitadel-network:
    driver: bridge
```

### 3. Create Environment Configuration

Create a `.env` file:

```bash
# Generate a secure master key
ZITADEL_MASTERKEY=$(openssl rand -base64 32)

# PostgreSQL password
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# SMTP Configuration (optional, for email notifications)
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com
```

### 4. Create Instance Configuration

Create `config/instance-config.yaml`:

```yaml
FirstInstance:
  Org:
    Name: 'Your Organization'
    Human:
      UserName: 'admin@yourdomain.com'
      FirstName: 'Admin'
      LastName: 'User'
      Email:
        Address: 'admin@yourdomain.com'
        Verified: true
      Password: 'ChangeMeImmediately123!'
```

### 5. Create Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream zitadel {
        server zitadel:8080;
    }

    server {
        listen 80;
        server_name auth.yourdomain.com;
        
        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    server {
        listen 443 ssl http2;
        server_name auth.yourdomain.com;

        ssl_certificate /etc/nginx/certs/fullchain.pem;
        ssl_certificate_key /etc/nginx/certs/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location / {
            proxy_pass http://zitadel;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

### 6. Start Zitadel

```bash
# Load environment variables
export $(cat .env | xargs)

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f zitadel
```

## Configuring Zitadel

### 1. Access Zitadel Console

Navigate to `https://auth.yourdomain.com` and log in with the admin credentials from `instance-config.yaml`.

### 2. Create a New Project

1. Go to **Projects** → **Create New Project**
2. Name: "Open edX Integration"
3. Click **Create**

### 3. Create an Application

1. In the project, click **New Application**
2. Name: "Open edX"
3. Type: **Web Application**
4. Authentication Method: **OIDC (OpenID Connect)**
5. Click **Continue**

### 4. Configure OIDC Settings

1. **Grant Types**: Authorization Code, Refresh Token
2. **Response Types**: Code
3. **Redirect URIs**: 
   - `https://your-openedx-domain.com/auth/complete/oidc/`
   - `https://your-openedx-domain.com/auth/complete/zitadel/`
4. **Post Logout URIs**: `https://your-openedx-domain.com/logout`
5. **Auth Method**: Basic
6. Click **Save**

### 5. Note Client Credentials

After saving, note down:
- **Client ID**
- **Client Secret** (generate if not shown)

## Integrating Zitadel with Open edX

### 1. Install Required Packages

SSH into your Open edX instance:

```bash
# For Tutor installations
tutor exec lms bash

# Install social-auth packages
pip install social-auth-app-django social-auth-core[openidconnect]
```

### 2. Configure Open edX Settings

Create or edit `/edx/app/edxapp/lms.env.json`:

```json
{
    "FEATURES": {
        "ENABLE_THIRD_PARTY_AUTH": true,
        "ENABLE_OAUTH2_PROVIDER": true
    },
    "THIRD_PARTY_AUTH_BACKENDS": [
        "social_core.backends.open_id_connect.OpenIdConnectAuth"
    ],
    "SOCIAL_AUTH_OAUTH_SECRETS": {
        "oidc": "your-client-secret-from-zitadel"
    }
}
```

### 3. Create Custom Backend

Create `/edx/app/edxapp/edx-platform/common/djangoapps/third_party_auth/zitadel_backend.py`:

```python
from social_core.backends.open_id_connect import OpenIdConnectAuth


class ZitadelOAuth2(OpenIdConnectAuth):
    """Zitadel OAuth2 authentication backend"""
    name = 'zitadel'
    OIDC_ENDPOINT = 'https://auth.yourdomain.com'
    DEFAULT_SCOPE = ['openid', 'profile', 'email']
    
    def get_user_details(self, response):
        """Extract user details from Zitadel response"""
        return {
            'username': response.get('preferred_username', ''),
            'email': response.get('email', ''),
            'fullname': response.get('name', ''),
            'first_name': response.get('given_name', ''),
            'last_name': response.get('family_name', ''),
        }
```

### 4. Configure Provider in Django Admin

1. Access Django Admin: `https://your-openedx-domain.com/admin`
2. Navigate to **Third Party Auth** → **Provider Configuration**
3. Add new provider:
   - **Backend name**: `zitadel`
   - **Name**: `Zitadel`
   - **Slug**: `zitadel`
   - **Site**: Your site
   - **Client ID**: Your Zitadel client ID
   - **Other settings**:
```json
{
    "authorization_url": "https://auth.yourdomain.com/oauth/v2/authorize",
    "access_token_url": "https://auth.yourdomain.com/oauth/v2/token",
    "userinfo_url": "https://auth.yourdomain.com/oidc/v1/userinfo",
    "client_secret": "your-client-secret"
}
```

### 5. Update Authentication Pipeline

Edit `/edx/app/edxapp/lms.env.json`:

```json
{
    "SOCIAL_AUTH_PIPELINE": [
        "social_core.pipeline.social_auth.social_details",
        "social_core.pipeline.social_auth.social_uid",
        "social_core.pipeline.social_auth.auth_allowed",
        "social_core.pipeline.social_auth.social_user",
        "social_core.pipeline.user.get_username",
        "social_core.pipeline.user.create_user",
        "social_core.pipeline.social_auth.associate_user",
        "social_core.pipeline.social_auth.load_extra_data",
        "social_core.pipeline.user.user_details",
        "common.djangoapps.third_party_auth.pipeline.set_logged_in_cookies",
        "common.djangoapps.third_party_auth.pipeline.login_analytics"
    ]
}
```

### 6. Restart Open edX Services

```bash
# For Tutor
tutor local restart lms cms

# For native installation
sudo /edx/bin/supervisorctl restart lms cms
```

## Adding SMS OTP with Kavenegar

### 1. Create SMS OTP Service

Create `sms-otp-service/package.json`:

```json
{
  "name": "zitadel-sms-otp",
  "version": "1.0.0",
  "description": "SMS OTP service for Zitadel using Kavenegar",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "axios": "^1.4.0",
    "dotenv": "^16.0.3",
    "body-parser": "^1.20.2",
    "kavenegar": "^1.1.4"
  },
  "devDependencies": {
    "nodemon": "^2.0.22"
  }
}
```

### 2. Create SMS OTP Server

Create `sms-otp-service/server.js`:

```javascript
const express = require('express');
const axios = require('axios');
const bodyParser = require('body-parser');
const Kavenegar = require('kavenegar');
require('dotenv').config();

const app = express();
app.use(bodyParser.json());

// Initialize Kavenegar
const api = Kavenegar.KavenegarApi({
    apikey: process.env.KAVENEGAR_API_KEY
});

// Store OTP codes temporarily (use Redis in production)
const otpStore = new Map();

// Generate OTP
function generateOTP() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

// Webhook endpoint for Zitadel to request OTP
app.post('/webhook/send-otp', async (req, res) => {
    try {
        const { userId, phoneNumber, event } = req.body;
        
        // Verify webhook signature (implement based on Zitadel's webhook security)
        const signature = req.headers['x-zitadel-signature'];
        if (!verifyWebhookSignature(req.body, signature)) {
            return res.status(401).json({ error: 'Invalid signature' });
        }

        // Generate OTP
        const otp = generateOTP();
        const expiresAt = Date.now() + 5 * 60 * 1000; // 5 minutes
        
        // Store OTP
        otpStore.set(userId, { otp, expiresAt, phoneNumber });

        // Send SMS via Kavenegar
        api.Send({
            message: `Your verification code is: ${otp}`,
            sender: process.env.KAVENEGAR_SENDER || '10004346',
            receptor: phoneNumber
        }, function(response, status) {
            if (status === 200) {
                console.log('SMS sent successfully:', response);
                res.json({ success: true, message: 'OTP sent' });
            } else {
                console.error('SMS sending failed:', status);
                res.status(500).json({ error: 'Failed to send SMS' });
            }
        });

    } catch (error) {
        console.error('Error in send-otp:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Verify OTP endpoint
app.post('/webhook/verify-otp', async (req, res) => {
    try {
        const { userId, otp } = req.body;
        
        // Verify webhook signature
        const signature = req.headers['x-zitadel-signature'];
        if (!verifyWebhookSignature(req.body, signature)) {
            return res.status(401).json({ error: 'Invalid signature' });
        }

        // Check OTP
        const storedData = otpStore.get(userId);
        if (!storedData) {
            return res.status(404).json({ error: 'OTP not found' });
        }

        if (Date.now() > storedData.expiresAt) {
            otpStore.delete(userId);
            return res.status(400).json({ error: 'OTP expired' });
        }

        if (storedData.otp !== otp) {
            return res.status(400).json({ error: 'Invalid OTP' });
        }

        // OTP is valid
        otpStore.delete(userId);
        
        // Notify Zitadel about successful verification
        await notifyZitadelOTPSuccess(userId);
        
        res.json({ success: true, message: 'OTP verified' });

    } catch (error) {
        console.error('Error in verify-otp:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Webhook signature verification
function verifyWebhookSignature(payload, signature) {
    // Implement based on Zitadel's webhook security mechanism
    // This is a placeholder implementation
    const crypto = require('crypto');
    const expectedSignature = crypto
        .createHmac('sha256', process.env.WEBHOOK_SECRET)
        .update(JSON.stringify(payload))
        .digest('hex');
    
    return signature === expectedSignature;
}

// Notify Zitadel about successful OTP verification
async function notifyZitadelOTPSuccess(userId) {
    try {
        const response = await axios.post(
            `${process.env.ZITADEL_URL}/management/v1/users/${userId}/otp/verify`,
            { verified: true },
            {
                headers: {
                    'Authorization': `Bearer ${process.env.ZITADEL_API_TOKEN}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        return response.data;
    } catch (error) {
        console.error('Error notifying Zitadel:', error);
        throw error;
    }
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`SMS OTP service running on port ${PORT}`);
});
```

### 3. Create Environment Configuration

Create `sms-otp-service/.env`:

```bash
# Kavenegar Configuration
KAVENEGAR_API_KEY=your-kavenegar-api-key
KAVENEGAR_SENDER=10004346

# Zitadel Configuration
ZITADEL_URL=https://auth.yourdomain.com
ZITADEL_API_TOKEN=your-zitadel-api-token
WEBHOOK_SECRET=your-webhook-secret

# Server Configuration
PORT=3000
```

### 4. Configure Zitadel Actions

Create a Zitadel Action for SMS OTP:

```javascript
// Zitadel Action: SMS OTP Flow
function sendSMSOTP(ctx, api) {
    // Check if user has phone number
    if (!ctx.v1.user.phone || !ctx.v1.user.phoneVerified) {
        return;
    }

    // Check if SMS OTP is required for this login
    if (ctx.v1.authRequest.type !== 'oidc' || !requiresSMSOTP(ctx)) {
        return;
    }

    // Send webhook to SMS service
    api.v1.action.webhook({
        url: 'https://your-sms-service.com/webhook/send-otp',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Zitadel-Signature': generateWebhookSignature(ctx)
        },
        body: {
            userId: ctx.v1.user.id,
            phoneNumber: ctx.v1.user.phone,
            event: 'login_otp'
        }
    });

    // Require OTP verification
    api.v1.auth.requireOTP();
}

function requiresSMSOTP(ctx) {
    // Implement your logic for when to require SMS OTP
    // For example: always for Open edX logins
    return ctx.v1.authRequest.clientId === 'your-openedx-client-id';
}

function generateWebhookSignature(ctx) {
    // Implement signature generation
    return 'generated-signature';
}
```

### 5. Deploy SMS OTP Service with Docker

Create `sms-otp-service/Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["node", "server.js"]
```

Update main `docker-compose.yml`:

```yaml
  sms-otp:
    build: ./sms-otp-service
    environment:
      - KAVENEGAR_API_KEY=${KAVENEGAR_API_KEY}
      - ZITADEL_URL=http://zitadel:8080
      - ZITADEL_API_TOKEN=${ZITADEL_API_TOKEN}
      - WEBHOOK_SECRET=${WEBHOOK_SECRET}
    ports:
      - '3000:3000'
    depends_on:
      - zitadel
    networks:
      - zitadel-network
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Zitadel Won't Start
- Check PostgreSQL is running: `docker-compose ps postgres`
- Verify master key is set: `echo $ZITADEL_MASTERKEY`
- Check logs: `docker-compose logs zitadel`

#### 2. Open edX OAuth Error
- Verify redirect URIs match exactly
- Check client secret is correctly configured
- Ensure HTTPS is properly configured

#### 3. SMS Not Sending
- Verify Kavenegar API key
- Check phone number format (international format required)
- Monitor SMS service logs: `docker-compose logs sms-otp`

#### 4. CORS Issues
Add CORS configuration to Nginx:

```nginx
add_header 'Access-Control-Allow-Origin' 'https://your-openedx-domain.com' always;
add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
```

## Security Considerations

1. **SSL/TLS**: Always use HTTPS in production
2. **Secrets Management**: Use proper secret management tools (e.g., HashiCorp Vault)
3. **Network Security**: Implement proper firewall rules
4. **Rate Limiting**: Add rate limiting to prevent OTP abuse
5. **Monitoring**: Set up monitoring and alerting for all services
6. **Backup**: Regular backup of PostgreSQL database
7. **Updates**: Keep all components updated regularly

### Production Recommendations

1. Use managed PostgreSQL instead of containerized
2. Implement Redis for OTP storage instead of in-memory
3. Use container orchestration (Kubernetes) for high availability
4. Implement proper logging and monitoring (ELK stack, Prometheus)
5. Use CDN for static assets
6. Implement DDoS protection

## Additional Resources

- [Zitadel Documentation](https://zitadel.com/docs)
- [Open edX Authentication](https://docs.openedx.org/projects/edx-platform/en/latest/concepts/authentication.html)
- [Kavenegar API Documentation](https://kavenegar.com/rest.html)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)

## Support

For issues or questions:
1. Check Zitadel GitHub issues
2. Open edX community forums
3. Kavenegar support portal

---

Last updated: [Current Date]
Version: 1.0.0