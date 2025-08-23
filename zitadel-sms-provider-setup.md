# Zitadel v2.42.0 HTTP SMS Provider Setup Guide

This guide explains how to add and configure an HTTP SMS provider in Zitadel v2.42.0.

## Overview

As of Zitadel v2.42.0, while Twilio is the primary supported SMS provider, you can configure custom HTTP/webhook-based SMS providers. This allows integration with various SMS services through HTTP endpoints.

## Prerequisites

1. Zitadel v2.42.0 instance running
2. Admin access to your Zitadel instance
3. An SMS provider with HTTP API support
4. Bearer token for Zitadel API authentication

## Step 1: Create HTTP SMS Provider

Use the following curl command to create a new HTTP SMS provider:

```bash
curl -L 'https://$ZITADEL_DOMAIN/admin/v1/sms/http' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer $TOKEN' \
  -d '{
    "endpoint": "https://your-sms-webhook.example.com/send",
    "description": "Custom HTTP SMS Provider"
  }'
```

Replace:
- `$ZITADEL_DOMAIN`: Your Zitadel instance domain
- `$TOKEN`: Your Zitadel admin API token
- `endpoint`: Your SMS webhook URL
- `description`: A descriptive name for your provider

The response will include an `id` for the newly created provider:

```json
{
  "id": "provider-id-here",
  "endpoint": "https://your-sms-webhook.example.com/send",
  "description": "Custom HTTP SMS Provider"
}
```

## Step 2: Activate the SMS Provider

After creating the provider, activate it:

```bash
curl -L 'https://$ZITADEL_DOMAIN/admin/v1/sms/$PROVIDER_ID/_activate' \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer $TOKEN' \
  -d '{}'
```

Replace `$PROVIDER_ID` with the ID received in Step 1.

## Step 3: Understanding the Webhook Payload

When Zitadel sends an SMS, it POSTs a JSON payload to your webhook endpoint:

```json
{
  "contextInfo": {
    "eventType": "user.human.otp.sms.sent",
    "provider": {
      "id": "provider-id",
      "description": "Custom HTTP SMS Provider"
    },
    "recipient": {
      "phoneNumber": "+1234567890"
    }
  },
  "templateData": {
    "subject": "Your verification code",
    "content": "Your verification code is: {{.Code}}",
    "contentType": "text/plain"
  },
  "args": {
    "Code": "123456",
    "UserName": "john.doe",
    "DisplayName": "John Doe"
  }
}
```

## Step 4: Implementing the Webhook Endpoint

Your webhook endpoint must:
1. Accept POST requests with JSON payload
2. Parse the Zitadel payload
3. Extract phone number and message content
4. Send SMS via your provider
5. Return appropriate HTTP status codes

### Expected Response

Success:
```json
{
  "success": true,
  "messageId": "sms-12345"
}
```
HTTP Status: 200 OK

Error:
```json
{
  "success": false,
  "error": "Failed to send SMS"
}
```
HTTP Status: 400/500

## Configuration via Environment Variables

For Docker deployments, you can configure SMS providers through environment variables:

```yaml
environment:
  ZITADEL_NOTIFYPROVIDER_SMSPROVIDER_ENDPOINT: "https://your-sms-webhook.example.com/send"
  ZITADEL_NOTIFYPROVIDER_SMSPROVIDER_DESCRIPTION: "Custom SMS Provider"
```

## Troubleshooting

1. **Provider not sending SMS**: Check webhook logs and ensure it returns 200 OK
2. **Authentication errors**: Verify your Bearer token is valid
3. **Webhook not receiving requests**: Check firewall rules and SSL certificates
4. **Message formatting issues**: Ensure your webhook properly processes template variables

## Security Considerations

1. Use HTTPS for webhook endpoints
2. Implement authentication on your webhook
3. Validate incoming requests from Zitadel
4. Rate limit your SMS sending
5. Log all SMS requests for audit purposes

## Example Providers

Common SMS providers that can be integrated via HTTP:
- Twilio (native support + HTTP)
- Vonage/Nexmo
- MessageBird
- AWS SNS
- SendGrid SMS
- Custom SMPP gateways

## Notes

- Full webhook support is planned for Zitadel v4
- Current implementation in v2.42.0 has limited customization
- Always test in staging before production deployment