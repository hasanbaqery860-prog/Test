/**
 * Zitadel Action: SMS OTP Authentication
 * 
 * This action triggers SMS OTP verification for specified applications
 * Place this in Zitadel Console: Actions -> New Action -> Type: Post Authentication
 */

function smsOTPAuthentication(ctx, api) {
    // Configuration
    const SMS_SERVICE_URL = 'https://your-sms-service.com';
    const WEBHOOK_SECRET = 'your-webhook-secret';
    const OPENEDX_CLIENT_ID = 'your-openedx-client-id';
    
    // Check if action should run
    if (!shouldRequireSMSOTP(ctx)) {
        return;
    }
    
    // Verify user has phone number
    const phoneNumber = ctx.v1.user.phone;
    if (!phoneNumber || !ctx.v1.user.phoneVerified) {
        api.v1.user.setMetadata('sms_otp_required', 'phone_missing');
        return;
    }
    
    // Generate webhook signature
    const payload = {
        userId: ctx.v1.user.id,
        phoneNumber: phoneNumber,
        event: 'login_otp',
        timestamp: new Date().toISOString()
    };
    
    const signature = generateHMAC(JSON.stringify(payload), WEBHOOK_SECRET);
    
    // Send OTP request
    api.v1.action.http({
        url: `${SMS_SERVICE_URL}/webhook/send-otp`,
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Zitadel-Signature': signature
        },
        body: payload,
        timeout: 5000
    });
    
    // Set metadata to track OTP requirement
    api.v1.user.setMetadata('sms_otp_required', 'true');
    api.v1.user.setMetadata('sms_otp_sent_at', new Date().toISOString());
    
    // Require additional verification
    api.v1.authentication.require2FA();
}

function shouldRequireSMSOTP(ctx) {
    // Skip for service accounts
    if (ctx.v1.user.type === 'SERVICE') {
        return false;
    }
    
    // Check if already verified in this session
    if (ctx.v1.user.metadata?.sms_otp_verified === 'true') {
        const verifiedAt = new Date(ctx.v1.user.metadata.sms_otp_verified_at);
        const hoursSinceVerified = (new Date() - verifiedAt) / (1000 * 60 * 60);
        
        // Skip if verified within last 24 hours
        if (hoursSinceVerified < 24) {
            return false;
        }
    }
    
    // Require for Open edX logins
    if (ctx.v1.authRequest?.clientId === OPENEDX_CLIENT_ID) {
        return true;
    }
    
    // Check organization policy
    if (ctx.v1.org.metadata?.require_sms_otp === 'true') {
        return true;
    }
    
    // Check user-specific requirement
    if (ctx.v1.user.metadata?.require_sms_otp === 'true') {
        return true;
    }
    
    return false;
}

function generateHMAC(data, secret) {
    // This is a placeholder - Zitadel actions may have limited crypto functions
    // In production, use proper HMAC generation
    return 'generated-signature';
}

// Register the action
smsOTPAuthentication(ctx, api);