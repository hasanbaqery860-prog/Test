#!/bin/bash

BASE_URL="http://91.107.146.137:8000"
COOKIE_FILE="test_cookies.txt"

echo "Testing Authentication Flow"
echo "Base URL: $BASE_URL"
echo "=================================================="

# Clean up any existing cookie file
rm -f "$COOKIE_FILE"

# Step 1: Access the main page and capture cookies
echo -e "\n1. Accessing main page..."
curl -c "$COOKIE_FILE" -b "$COOKIE_FILE" -s -o /dev/null -w "Status: %{http_code}\n" "$BASE_URL/"

# Check if we have a session cookie
if grep -q "sessionid" "$COOKIE_FILE"; then
    echo "   ✓ Session cookie present"
    SESSION_COOKIE=$(grep "sessionid" "$COOKIE_FILE" | cut -f7)
    echo "   Session ID: ${SESSION_COOKIE:0:20}..."
else
    echo "   ✗ No session cookie found"
fi

# Step 2: Try to access login
echo -e "\n2. Accessing /login..."
LOGIN_RESPONSE=$(curl -c "$COOKIE_FILE" -b "$COOKIE_FILE" -s -o /dev/null -w "%{http_code}|%{redirect_url}" "$BASE_URL/login")

STATUS=$(echo "$LOGIN_RESPONSE" | cut -d'|' -f1)
REDIRECT=$(echo "$LOGIN_RESPONSE" | cut -d'|' -f2)

echo "   Status: $STATUS"
if [[ "$STATUS" == "301" || "$STATUS" == "302" ]]; then
    echo "   Redirects to: $REDIRECT"
    if [[ "$REDIRECT" == *"/auth/login/oidc/"* ]]; then
        echo "   ✓ Correctly redirects to OIDC endpoint"
    else
        echo "   ✗ Wrong redirect target!"
    fi
fi

# Step 3: Check OIDC endpoint
echo -e "\n3. Checking OIDC endpoint..."
OIDC_RESPONSE=$(curl -c "$COOKIE_FILE" -b "$COOKIE_FILE" -s -o /dev/null -w "%{http_code}|%{redirect_url}" "$BASE_URL/auth/login/oidc/")

STATUS=$(echo "$OIDC_RESPONSE" | cut -d'|' -f1)
REDIRECT=$(echo "$OIDC_RESPONSE" | cut -d'|' -f2)

echo "   Status: $STATUS"
if [[ "$STATUS" == "301" || "$STATUS" == "302" ]]; then
    echo "   Redirects to: $REDIRECT"
    if [[ "$REDIRECT" == *"zitadel"* || "$REDIRECT" == *"oauth"* ]]; then
        echo "   ✓ Redirects to Zitadel/OAuth provider"
    else
        echo "   ? Check if this is your SSO provider"
    fi
fi

# Step 4: Check session cookie after OIDC redirect
if grep -q "sessionid" "$COOKIE_FILE"; then
    NEW_SESSION_COOKIE=$(grep "sessionid" "$COOKIE_FILE" | tail -1 | cut -f7)
    echo "   ✓ Session cookie maintained: ${NEW_SESSION_COOKIE:0:20}..."
    if [[ "$NEW_SESSION_COOKIE" != "$SESSION_COOKIE" ]]; then
        echo "   ✓ Session cookie updated"
    else
        echo "   - Session cookie unchanged"
    fi
else
    echo "   ✗ Session cookie lost after OIDC redirect"
fi

# Step 5: Check auth complete endpoint
echo -e "\n4. Checking auth complete endpoint..."
COMPLETE_RESPONSE=$(curl -c "$COOKIE_FILE" -b "$COOKIE_FILE" -s -o /dev/null -w "%{http_code}|%{redirect_url}" "$BASE_URL/auth/complete/oidc/")

STATUS=$(echo "$COMPLETE_RESPONSE" | cut -d'|' -f1)
REDIRECT=$(echo "$COMPLETE_RESPONSE" | cut -d'|' -f2)

echo "   Status: $STATUS"
if [[ "$STATUS" == "400" ]]; then
    echo "   ✓ Endpoint exists (400 is expected without valid OAuth response)"
elif [[ "$STATUS" == "404" ]]; then
    echo "   ✗ Endpoint not found - third party auth might not be enabled"
elif [[ "$STATUS" == "301" || "$STATUS" == "302" ]]; then
    echo "   Redirects to: $REDIRECT"
fi

# Step 6: Check final session state
echo -e "\n5. Final session state..."
if grep -q "sessionid" "$COOKIE_FILE"; then
    FINAL_SESSION_COOKIE=$(grep "sessionid" "$COOKIE_FILE" | tail -1 | cut -f7)
    echo "   ✓ Final session cookie: ${FINAL_SESSION_COOKIE:0:20}..."
else
    echo "   ✗ No final session cookie"
fi

# Step 7: Check if we can access protected content
echo -e "\n6. Testing protected content access..."
DASHBOARD_RESPONSE=$(curl -c "$COOKIE_FILE" -b "$COOKIE_FILE" -s -o /dev/null -w "%{http_code}|%{redirect_url}" "$BASE_URL/dashboard")

STATUS=$(echo "$DASHBOARD_RESPONSE" | cut -d'|' -f1)
REDIRECT=$(echo "$DASHBOARD_RESPONSE" | cut -d'|' -f2)

echo "   Dashboard status: $STATUS"
if [[ "$STATUS" == "200" ]]; then
    echo "   ✓ Dashboard accessible (user authenticated)"
elif [[ "$STATUS" == "301" || "$STATUS" == "302" ]]; then
    echo "   Redirects to: $REDIRECT"
    if [[ "$REDIRECT" == *"/login"* || "$REDIRECT" == *"/auth"* ]]; then
        echo "   ✗ User not authenticated - redirected to login"
    else
        echo "   ? Unexpected redirect"
    fi
else
    echo "   ? Unexpected status: $STATUS"
fi

# Step 8: Check cookie domain settings
echo -e "\n7. Cookie domain analysis..."
if grep -q "sessionid" "$COOKIE_FILE"; then
    COOKIE_LINE=$(grep "sessionid" "$COOKIE_FILE" | tail -1)
    DOMAIN=$(echo "$COOKIE_LINE" | cut -f6)
    echo "   Cookie domain: '$DOMAIN'"
    
    if [[ "$DOMAIN" == "local.openedx.io" ]]; then
        echo "   ❌ Problem: Cookie domain set to 'local.openedx.io' but accessing via IP"
        echo "   This will prevent session persistence!"
    elif [[ "$DOMAIN" == "" ]]; then
        echo "   ✅ Good: Cookie domain is empty (works with IP addresses)"
    else
        echo "   ? Check if domain '$DOMAIN' matches your access method"
    fi
else
    echo "   No session cookie found to analyze"
fi

echo -e "\n=================================================="
echo -e "\nDiagnosis:"
if [[ "$DOMAIN" == "local.openedx.io" ]]; then
    echo "❌ Session cookie domain mismatch - this is the root cause!"
    echo "   The session cookie is set for 'local.openedx.io' but you're accessing via IP"
    echo "   This prevents the browser from sending the session cookie back"
else
    echo "✅ Session cookie domain looks correct"
fi

echo -e "\nRecommendations:"
echo "1. Set SESSION_COOKIE_DOMAIN = None in Django settings"
echo "2. Restart the Open edX services after configuration change"
echo "3. Clear browser cookies and try again"
echo "4. Consider accessing via domain name instead of IP address"

# Clean up
rm -f "$COOKIE_FILE"