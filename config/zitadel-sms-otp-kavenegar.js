/**
 * Zitadel Action: SMS OTP with Kavenegar
 * 
 * Complete implementation for SMS OTP using Kavenegar API
 * Add this action to your Login flow in Zitadel Console
 */

import { http } from "zitadel";

// ===== CONFIGURATION - UPDATE THESE VALUES =====
const KAVENEGAR_API_KEY = "YOUR_KAVENEGAR_API_KEY"; // Your Kavenegar API key
const KAVENEGAR_SENDER = "10004346"; // Your Kavenegar sender number
const OPENEDX_CLIENT_ID = "YOUR_OPENEDX_CLIENT_ID"; // Client ID from Zitadel application

// ===== MAIN SMS OTP FUNCTION =====
export async function sendSMSOTP(ctx, api) {
    // Only run for Open edX logins
    if (ctx.v1.authRequest?.clientId !== OPENEDX_CLIENT_ID) {
        return;
    }
    
    // Check if OTP was already verified recently (24 hours)
    const lastVerified = ctx.v1.user?.metadata?.otp_verified_at;
    if (lastVerified) {
        const hoursSince = (Date.now() - new Date(lastVerified).getTime()) / (1000 * 60 * 60);
        if (hoursSince < 24) {
            console.log("OTP recently verified, skipping");
            return;
        }
    }
    
    // Get user's phone number
    const phone = ctx.v1.user?.phone;
    const phoneVerified = ctx.v1.user?.phoneVerified;
    
    if (!phone) {
        console.error("User has no phone number");
        api.v1.user.setMetadata("otp_error", "no_phone");
        // Optionally deny access or continue without OTP
        // api.v1.authentication.deny("Phone number required for login");
        return;
    }
    
    if (!phoneVerified) {
        console.warn("Phone number not verified");
        // Optionally require verification
        // api.v1.authentication.deny("Please verify your phone number first");
    }
    
    // Generate 6-digit OTP
    const otp = Math.floor(100000 + Math.random() * 900000).toString();
    
    // Store OTP with metadata
    const now = new Date();
    const expiresAt = new Date(now.getTime() + 5 * 60 * 1000); // 5 minutes
    
    api.v1.user.setMetadata("otp_code", otp);
    api.v1.user.setMetadata("otp_expires", expiresAt.toISOString());
    api.v1.user.setMetadata("otp_attempts", "0");
    api.v1.user.setMetadata("otp_sent_at", now.toISOString());
    
    // Format phone for Kavenegar (remove + and spaces)
    const formattedPhone = phone.replace(/[\s+]/g, '');
    
    // Prepare SMS message
    const message = `Your Open edX verification code is: ${otp}\nThis code expires in 5 minutes.`;
    
    try {
        // Send SMS via Kavenegar API
        const response = await http.post({
            url: `https://api.kavenegar.com/v1/${KAVENEGAR_API_KEY}/sms/send.json`,
            headers: { 
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            },
            body: `receptor=${formattedPhone}&sender=${KAVENEGAR_SENDER}&message=${encodeURIComponent(message)}`
        });
        
        // Parse response
        const result = JSON.parse(response.body);
        
        if (result.return?.status === 200) {
            console.log("SMS sent successfully to", formattedPhone);
            api.v1.user.setMetadata("otp_status", "sent");
            api.v1.user.setMetadata("otp_message_id", result.entries?.[0]?.messageid || "");
            
            // Require OTP verification
            api.v1.authentication.requireMFA();
            
        } else {
            console.error("Kavenegar error:", result.return?.message);
            api.v1.user.setMetadata("otp_status", "send_failed");
            api.v1.user.setMetadata("otp_error", result.return?.message || "unknown_error");
            
            // Decide whether to block login on SMS failure
            // api.v1.authentication.deny("Failed to send verification code");
        }
        
    } catch (error) {
        console.error("Failed to send SMS:", error);
        api.v1.user.setMetadata("otp_status", "send_error");
        api.v1.user.setMetadata("otp_error", error.message);
        
        // Decide whether to block login on SMS failure
        // api.v1.authentication.deny("Failed to send verification code");
    }
}

// ===== OTP VERIFICATION FUNCTION =====
export async function verifyOTP(ctx, api) {
    // Check if OTP verification is pending
    const otpStatus = ctx.v1.user?.metadata?.otp_status;
    if (otpStatus !== "sent") {
        return;
    }
    
    // Get stored OTP data
    const storedCode = ctx.v1.user?.metadata?.otp_code;
    const expiresAt = ctx.v1.user?.metadata?.otp_expires;
    const attempts = parseInt(ctx.v1.user?.metadata?.otp_attempts || "0");
    
    if (!storedCode || !expiresAt) {
        api.v1.authentication.deny("No verification code found");
        return;
    }
    
    // Check expiry
    if (new Date() > new Date(expiresAt)) {
        cleanupOTPData(api);
        api.v1.user.setMetadata("otp_status", "expired");
        api.v1.authentication.deny("Verification code has expired");
        return;
    }
    
    // Check max attempts
    if (attempts >= 3) {
        cleanupOTPData(api);
        api.v1.user.setMetadata("otp_status", "too_many_attempts");
        api.v1.authentication.deny("Too many failed attempts. Please request a new code.");
        return;
    }
    
    // Get user's OTP input
    const userInput = ctx.v1.mfa?.code || ctx.v1.authentication?.otpCode;
    
    if (!userInput) {
        // No input yet, increment attempts and wait
        api.v1.user.setMetadata("otp_attempts", (attempts + 1).toString());
        api.v1.authentication.requireMFA();
        return;
    }
    
    // Verify OTP
    if (userInput === storedCode) {
        // Success!
        cleanupOTPData(api);
        api.v1.user.setMetadata("otp_status", "verified");
        api.v1.user.setMetadata("otp_verified_at", new Date().toISOString());
        
        console.log("OTP verified successfully");
        
        // Allow login to proceed
        api.v1.authentication.allow();
        
    } else {
        // Failed attempt
        const newAttempts = attempts + 1;
        api.v1.user.setMetadata("otp_attempts", newAttempts.toString());
        
        if (newAttempts >= 3) {
            cleanupOTPData(api);
            api.v1.user.setMetadata("otp_status", "too_many_attempts");
            api.v1.authentication.deny("Too many failed attempts");
        } else {
            api.v1.authentication.deny(`Invalid code. ${3 - newAttempts} attempts remaining.`);
        }
    }
}

// ===== HELPER FUNCTION =====
function cleanupOTPData(api) {
    api.v1.user.removeMetadata("otp_code");
    api.v1.user.removeMetadata("otp_expires");
    api.v1.user.removeMetadata("otp_attempts");
    api.v1.user.removeMetadata("otp_sent_at");
    api.v1.user.removeMetadata("otp_message_id");
}

// ===== OPTIONAL: RESEND OTP FUNCTION =====
export async function resendOTP(ctx, api) {
    // Check if resend is allowed (e.g., after 60 seconds)
    const sentAt = ctx.v1.user?.metadata?.otp_sent_at;
    if (sentAt) {
        const secondsSince = (Date.now() - new Date(sentAt).getTime()) / 1000;
        if (secondsSince < 60) {
            api.v1.authentication.deny(`Please wait ${Math.ceil(60 - secondsSince)} seconds before requesting a new code`);
            return;
        }
    }
    
    // Clean up old data
    cleanupOTPData(api);
    
    // Trigger new OTP send
    await sendSMSOTP(ctx, api);
}