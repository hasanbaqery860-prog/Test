# Zitadel SMS Provider Setup with Phone Number + OTP Login

## Step 1: Add SMS Provider in Zitadel

### Option A: Using Admin Console

1. Login to Zitadel Admin Console
2. Go to **Instance** → **SMS Providers** (or **Settings** → **SMS Provider**)
3. Click **Add SMS Provider**
4. Choose provider type:
   - **Twilio** (built-in support)
   - **HTTP** (for custom providers like Kavenegar)

### For HTTP/Custom Provider (Kavenegar):

1. Select **HTTP** as provider type
2. Configure:
   ```
   Name: Kavenegar
   Endpoint: https://api.kavenegar.com/v1/{API_KEY}/sms/send.json
   Method: POST
   Headers:
     Content-Type: application/x-www-form-urlencoded
   ```

3. Configure Request Body Template:
   ```
   receptor={{.Phone}}&sender=30008077778888&message={{.Message}}
   ```

4. Replace `{API_KEY}` in the endpoint with your actual Kavenegar API key

### Option B: Using Configuration File

Add to your Zitadel configuration:

```yaml
SMSProvider:
  Type: HTTP
  HTTP:
    Endpoint: "https://api.kavenegar.com/v1/YOUR_API_KEY/sms/send.json"
    Method: POST
    Headers:
      Content-Type: "application/x-www-form-urlencoded"
    Body: "receptor={{.Phone}}&sender=30008077778888&message={{.Message}}"
```

## Step 2: Enable Passwordless Authentication

1. Go to **Instance** → **Login Policy** (or **Settings** → **Login Policy**)
2. Enable:
   - **Passwordless** / **Passwordless Login**
   - **SMS OTP** or **Phone verification**
3. Set **Passwordless Type**: SMS

## Step 3: Configure Login Settings

1. Go to **Instance** → **Login Settings**
2. Enable:
   - **Allow Register** (if you want users to register with phone)
   - **Passwordless with SMS**
3. Disable:
   - **Username Password** (if you want ONLY phone + OTP)

## Step 4: Set Authentication Policy

1. Go to your **Project** → **Authentication Policy**
2. Enable:
   - **Passwordless authentication**
   - **SMS as passwordless method**

## Step 5: Configure Your Application

1. In your Open edX application settings in Zitadel:
2. Under **Login Settings**:
   - Enable **Passwordless**
   - Set **Passwordless Type**: SMS

## Step 6: User Registration/Login Flow

### For New Users:
1. User enters phone number
2. Zitadel sends OTP via SMS
3. User enters OTP
4. Account created and logged in

### For Existing Users:
1. User enters phone number
2. Receives OTP
3. Enters OTP to login

## Environment Variables for Docker

Add to your docker-compose.yml:

```yaml
environment:
  # Enable passwordless
  - ZITADEL_DEFAULTINSTANCE_PASSWORDLESSENABLED=true
  - ZITADEL_DEFAULTINSTANCE_PASSWORDLESSTYPE=sms
  
  # SMS Provider Config
  - ZITADEL_NOTIFICIATIONS_PROVIDERS_SMS_HTTP_ENDPOINT=https://api.kavenegar.com/v1/YOUR_API_KEY/sms/send.json
  - ZITADEL_NOTIFICIATIONS_PROVIDERS_SMS_HTTP_METHOD=POST
```

## API Configuration (if needed)

To enable phone + OTP programmatically:

```bash
# Add passwordless authentication
curl -X POST https://your-zitadel/management/v1/users/{userId}/passwordless \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "type": "PASSWORDLESS_TYPE_SMS"
  }'
```

## Testing

1. Go to your login page
2. You should see "Login with Phone Number" option
3. Enter phone number
4. Receive OTP
5. Enter OTP to login

## Important Notes

- Phone numbers must be in international format (e.g., +98XXXXXXXXXX for Iran)
- OTP codes expire after 5 minutes by default
- Users need verified phone numbers
- You can set SMS OTP as the ONLY authentication method by disabling other methods