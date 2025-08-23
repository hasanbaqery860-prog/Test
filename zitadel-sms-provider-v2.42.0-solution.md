# Zitadel v2.42.0 SMS Provider Solutions

## ⚠️ Important: Version Limitation

**Zitadel v2.42.0 does NOT support HTTP SMS providers.** This feature was introduced in v2.55.1.

In v2.42.0, only Twilio is supported as an SMS provider through environment variables or configuration files.

## Available Options for v2.42.0

### Option 1: Use Twilio (Native Support)

Zitadel v2.42.0 has built-in support for Twilio. Configure it using environment variables:

```yaml
# Docker Compose example
environment:
  ZITADEL_NOTIFYPROVIDER_TWILIOAPIKEY: "your-twilio-account-sid"
  ZITADEL_NOTIFYPROVIDER_TWILIOAUTHTOKEN: "your-twilio-auth-token"
  ZITADEL_NOTIFYPROVIDER_TWILIOSENDERID: "+1234567890"
```

Or in your Zitadel configuration file:

```yaml
NotifyProvider:
  TwilioAPIKey: "your-twilio-account-sid"
  TwilioAuthToken: "your-twilio-auth-token"
  TwilioSenderID: "+1234567890"
```

### Option 2: Twilio Proxy (Workaround)

If you need to use a different SMS provider, you can create a proxy service that:
1. Pretends to be Twilio API
2. Receives SMS requests from Zitadel
3. Forwards them to your preferred SMS provider

### Option 3: Upgrade to v2.55.1+

The cleanest solution is to upgrade Zitadel to v2.55.1 or later, which supports HTTP SMS providers.

## Twilio Proxy Implementation

Here's a proxy service that intercepts Twilio API calls and forwards them to other providers:

```python
# Save as twilio-proxy.py
from flask import Flask, request, jsonify, Response
import requests
import os
from urllib.parse import parse_qs

app = Flask(__name__)

# Your actual SMS provider configuration
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'messagebird')  # messagebird, vonage, custom
MESSAGEBIRD_ACCESS_KEY = os.getenv('MESSAGEBIRD_ACCESS_KEY')
VONAGE_API_KEY = os.getenv('VONAGE_API_KEY')
VONAGE_API_SECRET = os.getenv('VONAGE_API_SECRET')

@app.route('/2010-04-01/Accounts/<account_sid>/Messages.json', methods=['POST'])
def handle_twilio_sms(account_sid):
    """Intercept Twilio API calls and forward to actual SMS provider"""
    
    # Parse Twilio format data
    data = parse_qs(request.get_data(as_text=True))
    to_number = data.get('To', [''])[0]
    from_number = data.get('From', [''])[0]
    body = data.get('Body', [''])[0]
    
    print(f"Intercepted SMS: To={to_number}, Body={body}")
    
    try:
        # Forward to actual SMS provider
        if SMS_PROVIDER == 'messagebird':
            send_via_messagebird(to_number, body)
        elif SMS_PROVIDER == 'vonage':
            send_via_vonage(to_number, body)
        # Add more providers as needed
        
        # Return Twilio-compatible response
        return Response(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<TwilioResponse>'
            '<Message>'
            '<Sid>PROXY1234567890</Sid>'
            '<Status>queued</Status>'
            '</Message>'
            '</TwilioResponse>',
            mimetype='application/xml'
        )
    except Exception as e:
        print(f"Error forwarding SMS: {e}")
        return jsonify({"error": str(e)}), 500

def send_via_messagebird(to, body):
    """Forward to MessageBird"""
    response = requests.post(
        'https://rest.messagebird.com/messages',
        headers={'Authorization': f'AccessKey {MESSAGEBIRD_ACCESS_KEY}'},
        json={
            'originator': 'Zitadel',
            'recipients': [to.replace('+', '')],
            'body': body
        }
    )
    response.raise_for_status()

def send_via_vonage(to, body):
    """Forward to Vonage"""
    response = requests.post(
        'https://rest.nexmo.com/sms/json',
        data={
            'api_key': VONAGE_API_KEY,
            'api_secret': VONAGE_API_SECRET,
            'from': 'Zitadel',
            'to': to,
            'text': body
        }
    )
    response.raise_for_status()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443, ssl_context='adhoc')
```

## Setting Up the Twilio Proxy

1. **Deploy the proxy service**
2. **Configure Zitadel to use your proxy as Twilio:**

```yaml
environment:
  # Point to your proxy instead of api.twilio.com
  ZITADEL_NOTIFYPROVIDER_TWILIOBASEURL: "https://your-proxy-domain.com"
  ZITADEL_NOTIFYPROVIDER_TWILIOAPIKEY: "dummy-account-sid"
  ZITADEL_NOTIFYPROVIDER_TWILIOAUTHTOKEN: "dummy-auth-token"
  ZITADEL_NOTIFYPROVIDER_TWILIOSENDERID: "+1234567890"
```

## Checking Your Zitadel Version

To verify your Zitadel version:

```bash
# Via API
curl https://your-zitadel-domain.com/admin/v1/healthz

# Via Docker
docker exec zitadel-container zitadel version

# Check logs
docker logs zitadel-container | grep -i version
```

## Upgrade Recommendation

For the best experience with custom SMS providers, we strongly recommend upgrading to Zitadel v2.55.1 or later:

1. **Backup your Zitadel instance**
2. **Review the upgrade guide**: https://zitadel.com/docs/self-hosting/manage/updating
3. **Test in a staging environment first**
4. **Perform the upgrade**

After upgrading to v2.55.1+, you can use the HTTP SMS provider feature:

```bash
curl -L 'https://$ZITADEL_DOMAIN/admin/v1/sms/http' \
  -H 'Authorization: Bearer $TOKEN' \
  -d '{
    "endpoint": "https://your-webhook.com/send",
    "description": "Custom SMS Provider"
  }'
```

## Summary

- **v2.42.0**: Only Twilio support (use proxy workaround for other providers)
- **v2.55.1+**: Full HTTP SMS provider support
- **Recommendation**: Upgrade to latest version for best flexibility