# Zitadel + Open edX Integration with SMS OTP

This repository contains a complete setup for integrating Zitadel (Identity Provider) with Open edX, including SMS OTP functionality using Kavenegar.

## Quick Start

1. **Clone and prepare**:
   ```bash
   cd zitadel-setup
   cp .env.example .env
   # Edit .env with your credentials
   ```

2. **Add SSL certificates**:
   ```bash
   mkdir -p certs
   # Copy your SSL certificates to certs/
   ```

3. **Start services**:
   ```bash
   ./start.sh
   ```

## Documentation

See [zitadel-openedx-integration-guide.md](./zitadel-openedx-integration-guide.md) for detailed setup instructions.

## Structure

```
.
├── docker-compose.yml          # Main Docker Compose configuration
├── .env.example               # Environment variables template
├── nginx.conf                 # Nginx reverse proxy configuration
├── config/
│   └── instance-config.yaml   # Zitadel initial configuration
├── sms-otp-service/          # SMS OTP service
│   ├── server.js             # Node.js OTP service
│   ├── package.json          # Dependencies
│   └── Dockerfile            # Container configuration
├── certs/                    # SSL certificates (not included)
└── zitadel-openedx-integration-guide.md  # Full documentation
```

## Services

- **Zitadel**: Identity and Access Management
- **PostgreSQL**: Database for Zitadel
- **Nginx**: Reverse proxy with SSL termination
- **SMS OTP Service**: Kavenegar integration for SMS OTP

## Support

For detailed instructions and troubleshooting, see the [full documentation](./zitadel-openedx-integration-guide.md).