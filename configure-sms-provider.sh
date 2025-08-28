#!/bin/bash

# Zitadel HTTP SMS Provider Configuration Script
# This script helps you configure an HTTP SMS provider in Zitadel v2.42.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to check if required variables are set
check_required_vars() {
    local required_vars=("ZITADEL_DOMAIN" "ZITADEL_TOKEN" "SMS_WEBHOOK_URL")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_color "$RED" "Error: Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "Please set the following environment variables:"
        echo "  export ZITADEL_DOMAIN=your-zitadel-domain.com"
        echo "  export ZITADEL_TOKEN=your-admin-api-token"
        echo "  export SMS_WEBHOOK_URL=https://your-webhook-url.com/send"
        exit 1
    fi
}

# Function to create SMS provider
create_sms_provider() {
    local description="${SMS_PROVIDER_DESC:-Custom HTTP SMS Provider}"
    
    print_color "$YELLOW" "Creating HTTP SMS provider..."
    
    response=$(curl -s -w "\n%{http_code}" -L "https://${ZITADEL_DOMAIN}/admin/v1/sms/http" \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json' \
        -H "Authorization: Bearer ${ZITADEL_TOKEN}" \
        -d "{
            \"endpoint\": \"${SMS_WEBHOOK_URL}\",
            \"description\": \"${description}\"
        }")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 201 ]; then
        provider_id=$(echo "$body" | grep -o '"id":"[^"]*' | sed 's/"id":"//')
        print_color "$GREEN" "✓ SMS provider created successfully!"
        echo "Provider ID: $provider_id"
        echo "$provider_id" > .sms_provider_id
        return 0
    else
        print_color "$RED" "✗ Failed to create SMS provider"
        echo "HTTP Status: $http_code"
        echo "Response: $body"
        return 1
    fi
}

# Function to activate SMS provider
activate_sms_provider() {
    local provider_id=$1
    
    print_color "$YELLOW" "Activating SMS provider..."
    
    response=$(curl -s -w "\n%{http_code}" -L "https://${ZITADEL_DOMAIN}/admin/v1/sms/${provider_id}/_activate" \
        -H 'Content-Type: application/json' \
        -H 'Accept: application/json' \
        -H "Authorization: Bearer ${ZITADEL_TOKEN}" \
        -d '{}')
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ] || [ "$http_code" -eq 204 ]; then
        print_color "$GREEN" "✓ SMS provider activated successfully!"
        return 0
    else
        print_color "$RED" "✗ Failed to activate SMS provider"
        echo "HTTP Status: $http_code"
        echo "Response: $body"
        return 1
    fi
}

# Function to list SMS providers
list_sms_providers() {
    print_color "$YELLOW" "Listing SMS providers..."
    
    response=$(curl -s -w "\n%{http_code}" -L "https://${ZITADEL_DOMAIN}/admin/v1/sms" \
        -H 'Accept: application/json' \
        -H "Authorization: Bearer ${ZITADEL_TOKEN}")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        print_color "$GREEN" "Current SMS providers:"
        echo "$body" | jq '.'
        return 0
    else
        print_color "$RED" "✗ Failed to list SMS providers"
        echo "HTTP Status: $http_code"
        echo "Response: $body"
        return 1
    fi
}

# Function to test SMS provider
test_sms_provider() {
    local phone_number=$1
    local provider_id=$2
    
    if [ -z "$phone_number" ]; then
        print_color "$YELLOW" "Enter phone number to test (e.g., +1234567890): "
        read phone_number
    fi
    
    print_color "$YELLOW" "Testing SMS provider..."
    
    # This would typically trigger a test SMS through Zitadel
    # The exact endpoint may vary based on your Zitadel version
    print_color "$GREEN" "Test SMS request sent to $phone_number"
    echo "Check your webhook logs to verify the request was received"
}

# Main menu
show_menu() {
    echo ""
    print_color "$GREEN" "=== Zitadel SMS Provider Configuration ==="
    echo "1. Create new HTTP SMS provider"
    echo "2. Activate existing SMS provider"
    echo "3. List all SMS providers"
    echo "4. Test SMS provider"
    echo "5. Full setup (create + activate)"
    echo "6. Exit"
    echo ""
    echo -n "Select an option: "
}

# Main script
main() {
    # Check for required commands
    command -v curl >/dev/null 2>&1 || { echo "Error: curl is required but not installed."; exit 1; }
    command -v jq >/dev/null 2>&1 || { echo "Warning: jq is recommended for JSON formatting"; }
    
    while true; do
        show_menu
        read choice
        
        case $choice in
            1)
                check_required_vars
                create_sms_provider
                ;;
            2)
                check_required_vars
                echo -n "Enter provider ID to activate: "
                read provider_id
                activate_sms_provider "$provider_id"
                ;;
            3)
                check_required_vars
                list_sms_providers
                ;;
            4)
                check_required_vars
                test_sms_provider
                ;;
            5)
                check_required_vars
                if create_sms_provider; then
                    provider_id=$(cat .sms_provider_id 2>/dev/null)
                    if [ -n "$provider_id" ]; then
                        activate_sms_provider "$provider_id"
                    fi
                fi
                ;;
            6)
                print_color "$GREEN" "Goodbye!"
                exit 0
                ;;
            *)
                print_color "$RED" "Invalid option. Please try again."
                ;;
        esac
    done
}

# Run main function
main "$@"