#!/bin/bash

# Zitadel v2.55.1 SMS Configuration Commands
# Based on the error "SMSConfig.NotExisting", we need to create the config first

ZITADEL_URL="http://91.107.146.137:8090"
TOKEN="TZKn-PfAcP2laWjAJGpH0ZgkE-ZicwtA7wCJ-hJY1XZSCvth07nYB43dOuifxpmMmzkhTvrDfZUmiEUXf_xiNkWmnf6TwAac-ljEEqbq"

echo "Configuring SMS Provider in Zitadel v2.55.1"
echo "==========================================="
echo ""

# Method 1: Try using instance notification settings
echo "Method 1: Configuring instance notification settings..."
curl -X PUT "$ZITADEL_URL/admin/v1/text/message/notification/sms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "providerType": "HTTP",
    "httpConfig": {
      "endpoint": "https://your-webhook.com/send"
    }
  }'

echo -e "\n\n"

# Method 2: Try setting SMS provider configuration directly
echo "Method 2: Setting SMS provider configuration..."
curl -X PUT "$ZITADEL_URL/admin/v1/instances/notification/providers/sms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "type": "HTTP",
    "config": {
      "endpoint": "https://your-webhook.com/send",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  }'

echo -e "\n\n"

# Method 3: Check if we need to use a PATCH instead
echo "Method 3: Using PATCH to update SMS configuration..."
curl -X PATCH "$ZITADEL_URL/admin/v1/policies/notification/providers/sms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "providerType": "HTTP",
    "httpEndpoint": "https://your-webhook.com/send"
  }'

echo -e "\n\n"

# Method 4: Try the settings endpoint
echo "Method 4: Using settings endpoint..."
curl -X POST "$ZITADEL_URL/admin/v1/settings/notification/sms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "provider": "HTTP",
    "http": {
      "endpoint": "https://your-webhook.com/send"
    }
  }'

echo -e "\n\n"

# Method 5: Check the actual API documentation
echo "Method 5: Getting API info..."
curl -X GET "$ZITADEL_URL/openapi/v2" \
  -H "Accept: application/json" 2>/dev/null | grep -i "sms" | head -20

echo -e "\n\n"

echo "If none of the above work, the SMS provider configuration might be:"
echo "1. Available only through the Zitadel Console UI"
echo "2. Require different permissions/roles"
echo "3. Need to be configured at the organization level instead of instance level"
echo ""
echo "Try accessing the Zitadel Console at: $ZITADEL_URL"
echo "Navigate to: Settings -> Notification Providers -> SMS"