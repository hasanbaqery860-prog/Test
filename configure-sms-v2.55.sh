#!/bin/bash

# Zitadel v2.55.1 SMS Provider Configuration Script

# Configuration
ZITADEL_URL="http://91.107.146.137:8090"
BEARER_TOKEN="TZKn-PfAcP2laWjAJGpH0ZgkE-ZicwtA7wCJ-hJY1XZSCvth07nYB43dOuifxpmMmzkhTvrDfZUmiEUXf_xiNkWmnf6TwAac-ljEEqbq"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Zitadel v2.55.1 SMS Provider Configuration ===${NC}"
echo ""

# Function to check SMS configuration
check_sms_config() {
    echo -e "${YELLOW}Checking current SMS configuration...${NC}"
    
    response=$(curl -s -w "\n%{http_code}" -L "$ZITADEL_URL/admin/v1/text/message/sms" \
        -H "Authorization: Bearer $BEARER_TOKEN" \
        -H "Accept: application/json")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    echo "Response code: $http_code"
    echo "Response body: $body"
    echo ""
}

# Function to create HTTP SMS provider
create_http_sms_provider() {
    local endpoint=$1
    local description=$2
    
    echo -e "${YELLOW}Creating HTTP SMS provider...${NC}"
    echo "Endpoint: $endpoint"
    echo "Description: $description"
    echo ""
    
    # First, let's try the correct endpoint with POST method
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -L "$ZITADEL_URL/admin/v1/text/message/sms/http" \
        -H "Authorization: Bearer $BEARER_TOKEN" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -d "{
            \"endpoint\": \"$endpoint\",
            \"description\": \"$description\"
        }")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✓ SMS provider created successfully!${NC}"
        echo "Response: $body"
        
        # Try to extract the ID
        provider_id=$(echo "$body" | grep -o '"id":"[^"]*' | sed 's/"id":"//')
        if [ -n "$provider_id" ]; then
            echo "Provider ID: $provider_id"
            echo "$provider_id" > .sms_provider_id
        fi
    else
        echo -e "${RED}✗ Failed to create SMS provider${NC}"
        echo "HTTP Code: $http_code"
        echo "Response: $body"
        
        # Try alternative endpoints
        echo ""
        echo -e "${YELLOW}Trying alternative endpoint...${NC}"
        
        # Try without /http suffix
        response2=$(curl -s -w "\n%{http_code}" -X POST \
            -L "$ZITADEL_URL/admin/v1/sms/providers" \
            -H "Authorization: Bearer $BEARER_TOKEN" \
            -H "Content-Type: application/json" \
            -H "Accept: application/json" \
            -d "{
                \"type\": \"HTTP\",
                \"endpoint\": \"$endpoint\",
                \"description\": \"$description\"
            }")
        
        http_code2=$(echo "$response2" | tail -n1)
        body2=$(echo "$response2" | sed '$d')
        
        echo "Alternative response code: $http_code2"
        echo "Alternative response: $body2"
    fi
}

# Function to list all available endpoints
discover_endpoints() {
    echo -e "${YELLOW}Discovering available SMS endpoints...${NC}"
    
    # Try to get API documentation or available endpoints
    endpoints=(
        "/admin/v1/sms"
        "/admin/v1/sms/providers"
        "/admin/v1/text/message/sms"
        "/admin/v1/settings/sms"
        "/management/v1/sms"
        "/management/v1/text/message/sms"
    )
    
    for endpoint in "${endpoints[@]}"; do
        echo -n "Checking $endpoint... "
        response=$(curl -s -o /dev/null -w "%{http_code}" \
            -L "$ZITADEL_URL$endpoint" \
            -H "Authorization: Bearer $BEARER_TOKEN")
        
        if [ "$response" != "404" ] && [ "$response" != "405" ]; then
            echo -e "${GREEN}Available (HTTP $response)${NC}"
            
            # Get more details
            full_response=$(curl -s -L "$ZITADEL_URL$endpoint" \
                -H "Authorization: Bearer $BEARER_TOKEN" \
                -H "Accept: application/json")
            echo "  Response: ${full_response:0:100}..."
        else
            echo -e "${RED}Not found${NC}"
        fi
    done
}

# Function to set SMS provider via settings
configure_sms_settings() {
    local endpoint=$1
    
    echo -e "${YELLOW}Trying to configure SMS via settings API...${NC}"
    
    # Try instance settings
    response=$(curl -s -w "\n%{http_code}" -X PUT \
        -L "$ZITADEL_URL/admin/v1/settings/sms" \
        -H "Authorization: Bearer $BEARER_TOKEN" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -d "{
            \"http\": {
                \"endpoint\": \"$endpoint\"
            }
        }")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    echo "Settings response code: $http_code"
    echo "Settings response: $body"
}

# Main execution
echo "1. Checking current SMS configuration..."
check_sms_config

echo ""
echo "2. Discovering available endpoints..."
discover_endpoints

echo ""
echo "3. Attempting to create HTTP SMS provider..."
echo -n "Enter SMS webhook endpoint URL: "
read webhook_url
echo -n "Enter description: "
read description

# Set defaults if empty
webhook_url=${webhook_url:-"https://your-webhook.com/send"}
description=${description:-"Custom HTTP SMS Provider"}

create_http_sms_provider "$webhook_url" "$description"

echo ""
echo "4. Trying settings-based configuration..."
configure_sms_settings "$webhook_url"

echo ""
echo -e "${GREEN}=== Configuration Summary ===${NC}"
echo "If the SMS provider was created successfully, you should now be able to use it."
echo "Check the Zitadel console or use the API to verify the configuration."
echo ""
echo "Next steps:"
echo "1. Deploy your SMS webhook to handle requests from Zitadel"
echo "2. Test SMS sending functionality"
echo "3. Monitor webhook logs for incoming requests"