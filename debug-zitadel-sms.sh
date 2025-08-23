#!/bin/bash

# Zitadel SMS Configuration Debugging Script
# This will help us find the correct way to configure SMS in your instance

ZITADEL_URL="http://91.107.146.137:8090"
TOKEN="TZKn-PfAcP2laWjAJGpH0ZgkE-ZicwtA7wCJ-hJY1XZSCvth07nYB43dOuifxpmMmzkhTvrDfZUmiEUXf_xiNkWmnf6TwAac-ljEEqbq"

echo "=== Zitadel SMS Configuration Debug ==="
echo "Instance: $ZITADEL_URL"
echo "======================================="
echo ""

# 1. Check instance info
echo "1. Checking instance information..."
curl -s "$ZITADEL_URL/admin/v1/instances" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.' 2>/dev/null || echo "Raw response:"

echo -e "\n---\n"

# 2. Get all available admin endpoints
echo "2. Listing all SMS-related endpoints..."
curl -s "$ZITADEL_URL/openapi/v2" \
  -H "Accept: application/json" 2>/dev/null | jq '.paths | keys[] | select(contains("sms") or contains("SMS") or contains("notification"))' 2>/dev/null || echo "OpenAPI not available"

echo -e "\n---\n"

# 3. Check notification policy
echo "3. Getting notification policy..."
curl -s "$ZITADEL_URL/admin/v1/policies/notification" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.' 2>/dev/null

echo -e "\n---\n"

# 4. Try management API instead of admin
echo "4. Trying management API..."
curl -s "$ZITADEL_URL/management/v1/policies/notification" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.' 2>/dev/null

echo -e "\n---\n"

# 5. Check instance features
echo "5. Checking instance features..."
curl -s "$ZITADEL_URL/admin/v1/features" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.' 2>/dev/null

echo -e "\n---\n"

# 6. Try to get SMS providers list
echo "6. Attempting to list SMS providers..."
endpoints=(
    "/admin/v1/sms-providers"
    "/admin/v1/providers/sms"
    "/admin/v1/notification-providers"
    "/admin/v1/settings/sms"
    "/admin/v1/instance/sms-providers"
)

for endpoint in "${endpoints[@]}"; do
    echo "Trying GET $endpoint..."
    response=$(curl -s -w "\nSTATUS:%{http_code}" "$ZITADEL_URL$endpoint" \
        -H "Authorization: Bearer $TOKEN" \
        -H "Accept: application/json")
    status=$(echo "$response" | grep "STATUS:" | cut -d: -f2)
    body=$(echo "$response" | sed '/STATUS:/d')
    
    if [ "$status" != "404" ] && [ "$status" != "405" ]; then
        echo "Found endpoint! Status: $status"
        echo "$body" | jq '.' 2>/dev/null || echo "$body"
    fi
done

echo -e "\n---\n"

# 7. Check text customization endpoints
echo "7. Checking text/message customization..."
curl -s "$ZITADEL_URL/admin/v1/text/default" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.messageTexts[] | select(.messageTextType | contains("SMS"))' 2>/dev/null

echo -e "\n---\n"

# 8. Try organization-level settings
echo "8. Checking organization settings..."
curl -s "$ZITADEL_URL/management/v1/orgs/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.' 2>/dev/null

echo -e "\n---\n"

# 9. Final attempt - check all settings
echo "9. Getting all instance settings..."
curl -s "$ZITADEL_URL/admin/v1/settings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/json" | jq '.' 2>/dev/null

echo -e "\n======================================="
echo "Debug complete. Please share the output to identify the correct configuration method."
echo ""
echo "Based on Zitadel v2.55.1, SMS configuration might be:"
echo "1. Only available through the Web Console"
echo "2. Configured during instance setup"
echo "3. Set via environment variables at startup"
echo "4. Available through a different API endpoint than documented"