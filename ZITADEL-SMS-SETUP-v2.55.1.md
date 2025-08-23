# Zitadel v2.55.1 SMS Provider Configuration Guide

## Problem
You're getting "SMSConfig.NotExisting" error when trying to configure HTTP SMS provider in Zitadel v2.55.1.

## Solution Options

### Option 1: Use Zitadel Console UI (Recommended)

The easiest way to configure SMS providers in v2.55.1 is through the web console:

1. **Access Zitadel Console**
   - Navigate to: http://91.107.146.137:8090
   - Login with your admin credentials

2. **Navigate to SMS Settings**
   - Go to: **Instance** → **Settings** → **Notification Providers**
   - Or: **Settings** → **SMS Provider**

3. **Configure HTTP Provider**
   - Select "HTTP" as provider type
   - Enter your webhook URL
   - Save the configuration

### Option 2: Check Correct API Endpoint

Run this diagnostic command first:

```bash
# Get current notification settings
curl -X GET "http://91.107.146.137:8090/admin/v1/policies/notification" \
  -H "Authorization: Bearer TZKn-PfAcP2laWjAJGpH0ZgkE-ZicwtA7wCJ-hJY1XZSCvth07nYB43dOuifxpmMmzkhTvrDfZUmiEUXf_xiNkWmnf6TwAac-ljEEqbq" \
  -H "Accept: application/json"
```

### Option 3: Initialize SMS Configuration First

The error suggests SMS config needs initialization. Try these commands in order:

```bash
# Step 1: Initialize notification policy
curl -X POST "http://91.107.146.137:8090/admin/v1/policies/notification" \
  -H "Authorization: Bearer TZKn-PfAcP2laWjAJGpH0ZgkE-ZicwtA7wCJ-hJY1XZSCvth07nYB43dOuifxpmMmzkhTvrDfZUmiEUXf_xiNkWmnf6TwAac-ljEEqbq" \
  -H "Content-Type: application/json" \
  -d '{
    "passwordChange": true
  }'

# Step 2: Set SMS provider
curl -X PUT "http://91.107.146.137:8090/admin/v1/policies/notification/providers/sms" \
  -H "Authorization: Bearer TZKn-PfAcP2laWjAJGpH0ZgkE-ZicwtA7wCJ-hJY1XZSCvth07nYB43dOuifxpmMmzkhTvrDfZUmiEUXf_xiNkWmnf6TwAac-ljEEqbq" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "http",
    "endpoint": "https://your-webhook.com/send"
  }'
```

### Option 4: Use Instance Settings

Try configuring at instance level:

```bash
# Configure instance SMS settings
curl -X PUT "http://91.107.146.137:8090/admin/v1/instances/default/sms" \
  -H "Authorization: Bearer TZKn-PfAcP2laWjAJGpH0ZgkE-ZicwtA7wCJ-hJY1XZSCvth07nYB43dOuifxpmMmzkhTvrDfZUmiEUXf_xiNkWmnf6TwAac-ljEEqbq" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "http",
    "http": {
      "endpoint": "https://your-webhook.com/send"
    }
  }'
```

## Webhook Implementation

Once configured, deploy your webhook using the provided `sms-webhook-example.py`:

```bash
# Deploy webhook
docker-compose up -d

# Your webhook will receive:
{
  "to": "+1234567890",
  "message": "Your OTP is: 123456",
  "templateId": "InitCode",
  "orgId": "...",
  "userId": "..."
}
```

## Troubleshooting Steps

1. **Verify Zitadel Version**
   ```bash
   curl http://91.107.146.137:8090/admin/v1/healthz
   ```

2. **Check API Documentation**
   ```bash
   curl http://91.107.146.137:8090/openapi/v2 | grep -i sms
   ```

3. **Test with Twilio First**
   Configure Twilio to ensure SMS functionality works:
   ```bash
   curl -X PUT "http://91.107.146.137:8090/admin/v1/policies/notification/providers/sms" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "type": "twilio",
       "twilioConfig": {
         "sid": "AC...",
         "token": "...",
         "senderNumber": "+1234567890"
       }
     }'
   ```

## Important Notes

1. **API Changes**: The SMS provider API may have changed between versions. The exact endpoint might be different in v2.55.1.

2. **Permissions**: Ensure your token has the necessary permissions:
   - `iam.policy.write`
   - `iam.instance.write`

3. **Console vs API**: Some features might only be available through the console in certain versions.

## Next Steps

1. **Try the Console UI first** - This is the most reliable method
2. **Run the diagnostic scripts** provided (`test-sms-endpoints.sh`)
3. **Check Zitadel logs** for more detailed error messages
4. **Contact Support** if the issue persists

## Alternative: Use Environment Variables

If API configuration fails, try environment variables during Zitadel startup:

```yaml
# docker-compose.yml
environment:
  ZITADEL_NOTIFICATIONPROVIDERS_SMS_PROVIDER: "http"
  ZITADEL_NOTIFICATIONPROVIDERS_SMS_HTTP_ENDPOINT: "https://your-webhook.com/send"
```

Remember: The exact configuration method may vary based on your Zitadel deployment method and version.