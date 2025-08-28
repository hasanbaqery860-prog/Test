#!/bin/bash

# Your Zitadel instance details
ZITADEL_URL="http://91.107.146.137:8090"
TOKEN="TZKn-PfAcP2laWjAJGpH0ZgkE-ZicwtA7wCJ-hJY1XZSCvth07nYB43dOuifxpmMmzkhTvrDfZUmiEUXf_xiNkWmnf6TwAac-ljEEqbq"

echo "Testing Zitadel v2.55.1 SMS Configuration Endpoints"
echo "=================================================="
echo ""

# Test 1: Check instance features
echo "1. Checking instance features..."
curl -X GET "$ZITADEL_URL/admin/v1/features" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.' || echo "No jq installed"

echo -e "\n\n"

# Test 2: Try to get current SMS settings
echo "2. Getting current SMS settings..."
curl -X GET "$ZITADEL_URL/admin/v1/policies/notification" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.' || echo "No jq installed"

echo -e "\n\n"

# Test 3: Try to create SMS provider with different endpoints
echo "3. Testing various SMS provider endpoints..."

# Endpoint variations to try
endpoints=(
  "/admin/v1/settings/sms/providers/http"
  "/admin/v1/instances/sms/http"
  "/admin/v1/notification/providers/sms/http"
  "/management/v1/org/sms/http"
  "/admin/v1/policies/notification/providers/sms"
)

for endpoint in "${endpoints[@]}"; do
  echo -e "\nTrying POST to: $endpoint"
  response=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST "$ZITADEL_URL$endpoint" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d '{
      "endpoint": "https://webhook.example.com/sms",
      "description": "Test SMS Provider"
    }')
  
  http_code=$(echo "$response" | grep "HTTP_CODE:" | cut -d: -f2)
  body=$(echo "$response" | sed '/HTTP_CODE:/d')
  
  echo "Response Code: $http_code"
  echo "Response Body: $body" | jq '.' 2>/dev/null || echo "$body"
done

echo -e "\n\n"

# Test 4: Try to configure notification policy
echo "4. Trying to set notification policy..."
curl -X PUT "$ZITADEL_URL/admin/v1/policies/notification" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "passwordChange": true,
    "externalIdp": true,
    "smsProviderType": "HTTP",
    "smsProviderConfig": {
      "endpoint": "https://webhook.example.com/sms"
    }
  }' | jq '.' || echo "No jq installed"

echo -e "\n\n"

# Test 5: Check if it's an instance-level setting
echo "5. Checking instance settings..."
curl -X GET "$ZITADEL_URL/admin/v1/instances/default" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.' || echo "No jq installed"