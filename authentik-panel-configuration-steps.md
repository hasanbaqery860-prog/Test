# Detailed Authentik Panel Configuration Steps

## Step 1: Login to Authentik
1. Open your browser and navigate to `http://localhost:9000`
2. Login with your admin credentials

## Step 2: Create OAuth2/OpenID Connect Provider

1. **Navigate to Providers:**
   - In the left sidebar, click on **Applications**
   - Click on **Providers**
   - Click the **Create** button in the top right

2. **Select Provider Type:**
   - Choose **OAuth2/OpenID Provider**
   - Click **Next**

3. **Configure Basic Settings:**
   ```
   Name: Open edX Provider
   Authentication flow: default-provider-authorization-implicit-consent
   Authorization flow: default-provider-authorization-implicit-consent
   ```

4. **Configure Protocol Settings:**
   ```
   Client type: Confidential
   Client ID: openedx-oauth2-client
   Client Secret: [Click Generate or copy the auto-generated one]
   Redirect URIs/Origins (Regex): 
     - Add: http://local.openedx.io:8000/auth/complete/oidc/
     - Add: http://studio.local.openedx.io:8001/auth/complete/oidc/
     - Add: http://local.openedx.io:8000/oauth2/complete/oidc/
     - Add: http://studio.local.openedx.io:8001/oauth2/complete/oidc/
   ```

5. **Configure Advanced Protocol Settings:**
   ```
   Subject mode: Based on the User's hashed ID
   Include claims in id_token: ✓ (checked)
   Issuer mode: Same identifier is used for all providers
   ```

6. **Configure Machine-to-Machine Authentication:**
   ```
   Trusted OIDC Sources: [Leave empty]
   ```

7. **Scopes Configuration:**
   - Select the following scopes:
     - `openid` (Required)
     - `email` (Required)
     - `profile` (Required)
     - `offline_access` (Optional, for refresh tokens)

8. **Signing Key:**
   ```
   Signing Key: authentik Self-signed Certificate
   ```

9. Click **Finish** to save the provider

## Step 3: Create Application

1. **Navigate to Applications:**
   - In the left sidebar, under **Applications**, click **Applications**
   - Click the **Create** button

2. **Configure Application:**
   ```
   Name: Open edX
   Slug: openedx
   Group: [Leave empty or select appropriate group]
   Provider: Open edX Provider (select the provider you just created)
   Policy engine mode: any
   ```

3. **UI Settings:**
   ```
   Launch URL: http://local.openedx.io:8000/
   Icon: [Optional - you can upload an Open edX logo]
   Description: Open edX Learning Management System
   Publisher: [Your organization name]
   ```

4. Click **Create** to save the application

## Step 4: Verify Property Mappings

1. **Navigate to Property Mappings:**
   - In the left sidebar, click **Customization**
   - Click **Property Mappings**

2. **Verify these OIDC mappings exist:**
   - `authentik default OIDC Mapping: OpenID 'email'`
   - `authentik default OIDC Mapping: OpenID 'given_name'`
   - `authentik default OIDC Mapping: OpenID 'family_name'`
   - `authentik default OIDC Mapping: OpenID 'preferred_username'`
   - `authentik default OIDC Mapping: OpenID 'name'`

3. **If any are missing, create them:**
   - Click **Create**
   - Choose **OpenID Provider Mapping**
   - Configure as needed

## Step 5: Create Custom Scope Mappings (Optional but Recommended)

1. **Create Username Mapping:**
   ```
   Name: Open edX Username
   Scope name: openedx_username
   Expression: 
   return {
       "username": request.user.username,
       "preferred_username": request.user.username
   }
   ```

2. **Create Full Name Mapping:**
   ```
   Name: Open edX Full Name
   Scope name: openedx_fullname
   Expression:
   return {
       "name": request.user.name,
       "given_name": request.user.first_name,
       "family_name": request.user.last_name
   }
   ```

## Step 6: Test the OIDC Discovery Endpoint

1. Open a new browser tab
2. Navigate to: `http://localhost:9000/application/o/openedx/.well-known/openid-configuration`
3. You should see a JSON response with the OIDC configuration

## Step 7: Configure User Permissions (Important!)

1. **Create a Group for Open edX Users:**
   - Navigate to **Directory** → **Groups**
   - Click **Create**
   - Name: `Open edX Users`
   - Click **Create**

2. **Configure Application Access:**
   - Go back to **Applications** → **Applications**
   - Click on your **Open edX** application
   - Go to the **Policy / Group / User Bindings** tab
   - Click **Create Binding**
   - Select:
     - Group: `Open edX Users`
     - Enabled: ✓
   - Click **Create**

3. **Add Users to Group:**
   - Navigate to **Directory** → **Users**
   - For each user that should access Open edX:
     - Click on the user
     - Go to **Groups** tab
     - Add them to `Open edX Users` group

## Step 8: Important URLs to Note

After configuration, these are the important URLs:

1. **OIDC Discovery URL:**
   ```
   http://localhost:9000/application/o/openedx/.well-known/openid-configuration
   ```

2. **Authorization Endpoint:**
   ```
   http://localhost:9000/application/o/authorize/
   ```

3. **Token Endpoint:**
   ```
   http://localhost:9000/application/o/token/
   ```

4. **UserInfo Endpoint:**
   ```
   http://localhost:9000/application/o/userinfo/
   ```

5. **JWKS Endpoint:**
   ```
   http://localhost:9000/application/o/openedx/jwks/
   ```

## Step 9: Save Your Credentials

Make sure to save:
- **Client ID**: `openedx-oauth2-client`
- **Client Secret**: [The generated secret from Step 2]
- **OIDC Endpoint**: `http://localhost:9000/application/o/openedx/`

You'll need these for the Open edX configuration.

## Troubleshooting Tips

1. **If login fails with "redirect_uri_mismatch":**
   - Check that the redirect URIs in Authentik exactly match what Open edX sends
   - Common issue: trailing slashes or different protocols (http vs https)

2. **If users can't access the application:**
   - Ensure they're in the correct group
   - Check the application's policy bindings

3. **If claims are missing:**
   - Verify property mappings are assigned to the provider
   - Check that scopes are properly configured

4. **Enable debug logging in Authentik:**
   - Navigate to **System** → **Settings**
   - Set log level to `DEBUG` temporarily for troubleshooting