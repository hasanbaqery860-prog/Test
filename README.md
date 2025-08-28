# Zitadel SMS Provider Integration

This repository provides solutions for integrating SMS providers with Zitadel.

## ⚠️ IMPORTANT: Version Compatibility

- **Zitadel v2.42.0**: Only supports Twilio natively (use our proxy solution for other providers)
- **Zitadel v2.55.1+**: Supports HTTP SMS providers directly

**If you're using v2.42.0, please see [zitadel-sms-provider-v2.42.0-solution.md](./zitadel-sms-provider-v2.42.0-solution.md) for specific instructions.**

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Supported SMS Providers](#supported-sms-providers)
- [Installation](#installation)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Security](#security)

## 🎯 Overview

This repository provides multiple solutions for SMS integration with Zitadel:

### For Zitadel v2.42.0
- Twilio proxy solution to use non-Twilio SMS providers
- Configuration guides for native Twilio support

### For Zitadel v2.55.1+
- Direct HTTP SMS provider integration
- Webhook server for custom SMS providers

This solution provides:

- 🔌 Ready-to-use webhook server with support for multiple SMS providers
- 🛠️ Configuration scripts for easy Zitadel setup
- 🐳 Docker deployment with health checks and logging
- 🔒 Security best practices implementation

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Zitadel   │─────▶│   Webhook    │─────▶│ SMS Provider│
│   v2.42.0   │ HTTP │    Server    │ API  │  (Twilio,   │
└─────────────┘      └──────────────┘      │ MessageBird,│
                                           │   etc.)     │
                                           └─────────────┘
```

## 🚀 Quick Start

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd zitadel-sms-provider
   ```

2. **Set up environment variables:**
   ```bash
   export ZITADEL_DOMAIN=your-zitadel.com
   export ZITADEL_TOKEN=your-admin-token
   export SMS_WEBHOOK_URL=https://your-webhook.com/send
   ```

3. **Run the configuration script:**
   ```bash
   chmod +x configure-sms-provider.sh
   ./configure-sms-provider.sh
   ```

4. **Deploy the webhook server:**
   ```bash
   docker-compose up -d
   ```

## 📱 Supported SMS Providers

### Native Support
- **Twilio** - Full integration with Twilio API
- **MessageBird** - Direct MessageBird API support
- **Vonage (Nexmo)** - Vonage SMS API integration
- **Custom** - Any HTTP-based SMS API

### Configuration Examples

#### Twilio
```env
SMS_PROVIDER=twilio
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM_NUMBER=+1234567890
```

#### MessageBird
```env
SMS_PROVIDER=messagebird
MESSAGEBIRD_ACCESS_KEY=your-access-key
MESSAGEBIRD_FROM=YourBrand
```

#### Custom Provider
```env
SMS_PROVIDER=custom
CUSTOM_SMS_ENDPOINT=https://api.your-provider.com/send
CUSTOM_SMS_API_KEY=your-api-key
```

## 💾 Installation

### Prerequisites
- Docker and Docker Compose (for containerized deployment)
- Python 3.11+ (for local development)
- curl and jq (for configuration scripts)
- Valid Zitadel instance with admin access

### Local Development
```bash
# Install Python dependencies
pip install -r requirements.txt

# Run the webhook server
python sms-webhook-example.py
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f sms-webhook
```

## ⚙️ Configuration

### Zitadel Configuration

1. **Create SMS Provider:**
   ```bash
   curl -L 'https://$ZITADEL_DOMAIN/admin/v1/sms/http' \
     -H 'Authorization: Bearer $TOKEN' \
     -d '{
       "endpoint": "https://your-webhook.com/send",
       "description": "Custom SMS Provider"
     }'
   ```

2. **Activate Provider:**
   ```bash
   curl -L 'https://$ZITADEL_DOMAIN/admin/v1/sms/$PROVIDER_ID/_activate' \
     -H 'Authorization: Bearer $TOKEN' \
     -d '{}'
   ```

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `WEBHOOK_SECRET` | Authentication token for webhook | Yes |
| `SMS_PROVIDER` | Provider type (twilio, messagebird, etc.) | Yes |
| `PORT` | Webhook server port | No (default: 5000) |
| `DEBUG` | Enable debug logging | No (default: false) |

## 🚢 Deployment

### Production Deployment with SSL

1. **Create SSL certificates:**
   ```bash
   mkdir ssl
   # Add your SSL certificates to the ssl directory
   ```

2. **Create nginx configuration:**
   ```nginx
   server {
       listen 443 ssl;
       server_name your-webhook.com;
       
       ssl_certificate /etc/nginx/ssl/cert.pem;
       ssl_certificate_key /etc/nginx/ssl/key.pem;
       
       location / {
           proxy_pass http://sms-webhook:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. **Deploy with SSL:**
   ```bash
   docker-compose --profile with-ssl up -d
   ```

### Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests (if needed).

## 🧪 Testing

### Test the Webhook
```bash
# Test endpoint
curl -X POST http://localhost:5000/test \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-webhook-secret" \
  -d '{
    "contextInfo": {
      "recipient": {"phoneNumber": "+1234567890"}
    },
    "templateData": {
      "content": "Your code is: {{.Code}}"
    },
    "args": {
      "Code": "123456"
    }
  }'
```

### Monitor Logs
```bash
# Docker logs
docker-compose logs -f sms-webhook

# Local development
tail -f webhook.log
```

## 🔧 Troubleshooting

### Common Issues

1. **Provider not sending SMS**
   - Check webhook logs for errors
   - Verify provider credentials
   - Ensure webhook returns 200 OK

2. **Authentication errors**
   - Verify Bearer token matches WEBHOOK_SECRET
   - Check Zitadel admin token is valid

3. **Connection errors**
   - Verify firewall rules allow outbound HTTPS
   - Check SSL certificates are valid
   - Ensure webhook URL is accessible from Zitadel

### Debug Mode
```bash
# Enable debug logging
export DEBUG=true
docker-compose up
```

## 🔒 Security

### Best Practices

1. **Use HTTPS** - Always use SSL/TLS in production
2. **Authenticate requests** - Verify webhook secret on all requests
3. **Rate limiting** - Implement rate limits to prevent abuse
4. **Log security events** - Monitor for suspicious activity
5. **Rotate secrets** - Regularly update authentication tokens

### Security Headers
The webhook implements these security measures:
- Bearer token authentication
- Request validation
- Error message sanitization
- Secure logging practices

## 📚 Additional Resources

- [Zitadel Documentation](https://zitadel.com/docs)
- [Provider Setup Guide](./zitadel-sms-provider-setup.md)
- [API Reference](https://zitadel.com/docs/apis/introduction)

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

This project is provided as-is for educational and integration purposes.