#!/bin/bash

echo "Fixing MFE Configuration for Authentik..."

# Save configuration to apply the new patches
echo -e "\n1. Applying configuration patches:"
tutor config save

# Check if MFE plugin is enabled
echo -e "\n2. Checking if MFE plugin is enabled:"
tutor plugins list | grep mfe

# Rebuild MFE image with new configuration
echo -e "\n3. Rebuilding MFE image (this may take a few minutes):"
tutor images build mfe

# Restart services
echo -e "\n4. Restarting all services:"
tutor local stop
tutor local start -d

echo -e "\n5. Waiting for services to be ready..."
sleep 30

# Check the MFE configuration
echo -e "\n6. Verifying MFE configuration:"
tutor config printvalue MFE_CONFIG | grep -A10 "THIRD_PARTY"

echo -e "\n✅ Done! The Authentik button should now appear on the MFE login page."
echo -e "\nVisit: http://local.openedx.io:8000/authn/login"
echo -e "\nNote: You may need to clear your browser cache (Ctrl+Shift+R) to see the changes."