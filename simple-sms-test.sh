#!/bin/bash

# Simple SMS Configuration Test for Zitadel v2.55.1

ZITADEL_URL="http://91.107.146.137:8090"
TOKEN="TZKn-PfAcP2laWjAJGpH0ZgkE-ZicwtA7wCJ-hJY1XZSCvth07nYB43dOuifxpmMmzkhTvrDfZUmiEUXf_xiNkWmnf6TwAac-ljEEqbq"

echo "=== Simple SMS Configuration Test ==="
echo ""

# Test 1: Basic health check
echo "1. Health check:"
curl -s "$ZITADEL_URL/admin/v1/healthz" | jq '.' 2>/dev/null || echo "Health check failed"

echo -e "\n---\n"

# Test 2: Try POST with explicit headers
echo "2. Attempting POST to /admin/v1/sms/http with all headers:"
curl -v -X POST "$ZITADEL_URL/admin/v1/sms/http" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "endpoint": "https://webhook.site/test",
    "description": "Test SMS Provider"
  }' 2>&1

echo -e "\n---\n"

# Test 3: Check if it's a PUT instead of POST
echo "3. Trying PUT method:"
curl -X PUT "$ZITADEL_URL/admin/v1/sms/http" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint": "https://webhook.site/test",
    "description": "Test SMS Provider"
  }'

echo -e "\n---\n"

# Test 4: Try without /http suffix
echo "4. Trying without /http suffix:"
curl -X POST "$ZITADEL_URL/admin/v1/sms" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "http",
    "endpoint": "https://webhook.site/test",
    "description": "Test SMS Provider"
  }'

echo -e "\n---\n"

# Test 5: Check what methods are allowed
echo "5. Checking allowed methods with OPTIONS:"
curl -X OPTIONS "$ZITADEL_URL/admin/v1/sms/http" \
  -H "Authorization: Bearer $TOKEN" -v 2>&1 | grep -i "allow:"

echo -e "\n\n=== IMPORTANT ==="
echo "If all API attempts fail, you have these options:"
echo ""
echo "1. USE THE WEB CONSOLE:"
echo "   - Go to: $ZITADEL_URL"
echo "   - Login as admin"
echo "   - Navigate to: Instance Settings > Notification > SMS Provider"
echo "   - Select 'HTTP' and enter your webhook URL"
echo ""
echo "2. CONFIGURE VIA ENVIRONMENT VARIABLES:"
echo "   When starting Zitadel, set:"
echo "   ZITADEL_NOTIFICATIONPROVIDERS_SMS_PROVIDER=http"
echo "   ZITADEL_NOTIFICATIONPROVIDERS_SMS_HTTP_ENDPOINT=https://your-webhook.com/send"
echo ""
echo "3. USE TWILIO:"
echo "   If HTTP isn't working, configure Twilio which is well-supported"
echo "   Then use the Twilio proxy solution we created"
echo ""
echo "=================="