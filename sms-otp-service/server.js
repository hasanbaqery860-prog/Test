const express = require('express');
const axios = require('axios');
const bodyParser = require('body-parser');
const Kavenegar = require('kavenegar');
const helmet = require('helmet');
const cors = require('cors');
const winston = require('winston');
const rateLimit = require('express-rate-limit');
const crypto = require('crypto');
require('dotenv').config();

// Configure logger
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.json(),
    defaultMeta: { service: 'sms-otp' },
    transports: [
        new winston.transports.File({ filename: 'error.log', level: 'error' }),
        new winston.transports.File({ filename: 'combined.log' }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

const app = express();

// Security middleware
app.use(helmet());
app.use(cors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:8080'],
    credentials: true
}));
app.use(bodyParser.json());

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100 // limit each IP to 100 requests per windowMs
});

const otpLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 5, // limit each IP to 5 OTP requests per windowMs
    message: 'Too many OTP requests, please try again later'
});

app.use('/webhook', limiter);
app.use('/webhook/send-otp', otpLimiter);

// Initialize Kavenegar
const api = Kavenegar.KavenegarApi({
    apikey: process.env.KAVENEGAR_API_KEY
});

// Store OTP codes temporarily (use Redis in production)
const otpStore = new Map();

// Clean up expired OTPs every 5 minutes
setInterval(() => {
    const now = Date.now();
    for (const [key, value] of otpStore.entries()) {
        if (now > value.expiresAt) {
            otpStore.delete(key);
        }
    }
}, 5 * 60 * 1000);

// Generate OTP
function generateOTP() {
    return Math.floor(100000 + Math.random() * 900000).toString();
}

// Webhook signature verification
function verifyWebhookSignature(payload, signature) {
    if (!signature || !process.env.WEBHOOK_SECRET) {
        return false;
    }
    
    const expectedSignature = crypto
        .createHmac('sha256', process.env.WEBHOOK_SECRET)
        .update(JSON.stringify(payload))
        .digest('hex');
    
    return crypto.timingSafeEqual(
        Buffer.from(signature),
        Buffer.from(expectedSignature)
    );
}

// Webhook endpoint for Zitadel to request OTP
app.post('/webhook/send-otp', async (req, res) => {
    try {
        const { userId, phoneNumber, event } = req.body;
        
        // Validate input
        if (!userId || !phoneNumber) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        // Verify webhook signature
        const signature = req.headers['x-zitadel-signature'];
        if (!verifyWebhookSignature(req.body, signature)) {
            logger.warn('Invalid webhook signature', { userId });
            return res.status(401).json({ error: 'Invalid signature' });
        }

        // Check if user already has pending OTP
        if (otpStore.has(userId)) {
            const existing = otpStore.get(userId);
            if (Date.now() < existing.expiresAt - 4 * 60 * 1000) { // If more than 1 minute left
                return res.status(429).json({ error: 'OTP already sent, please wait' });
            }
        }

        // Generate OTP
        const otp = generateOTP();
        const expiresAt = Date.now() + 5 * 60 * 1000; // 5 minutes
        
        // Store OTP
        otpStore.set(userId, { 
            otp, 
            expiresAt, 
            phoneNumber,
            attempts: 0,
            event 
        });

        // Format phone number for Kavenegar (remove + if present)
        const formattedPhone = phoneNumber.replace(/^\+/, '');

        // Send SMS via Kavenegar
        api.Send({
            message: `Your verification code is: ${otp}\nThis code will expire in 5 minutes.`,
            sender: process.env.KAVENEGAR_SENDER || '10004346',
            receptor: formattedPhone
        }, function(response, status) {
            if (status === 200) {
                logger.info('SMS sent successfully', { userId, phoneNumber: formattedPhone });
                res.json({ success: true, message: 'OTP sent' });
            } else {
                logger.error('SMS sending failed', { status, response });
                otpStore.delete(userId); // Clean up on failure
                res.status(500).json({ error: 'Failed to send SMS' });
            }
        });

    } catch (error) {
        logger.error('Error in send-otp:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Verify OTP endpoint
app.post('/webhook/verify-otp', async (req, res) => {
    try {
        const { userId, otp } = req.body;
        
        // Validate input
        if (!userId || !otp) {
            return res.status(400).json({ error: 'Missing required fields' });
        }

        // Verify webhook signature
        const signature = req.headers['x-zitadel-signature'];
        if (!verifyWebhookSignature(req.body, signature)) {
            logger.warn('Invalid webhook signature for verify', { userId });
            return res.status(401).json({ error: 'Invalid signature' });
        }

        // Check OTP
        const storedData = otpStore.get(userId);
        if (!storedData) {
            return res.status(404).json({ error: 'OTP not found or expired' });
        }

        // Check expiration
        if (Date.now() > storedData.expiresAt) {
            otpStore.delete(userId);
            return res.status(400).json({ error: 'OTP expired' });
        }

        // Check attempts
        storedData.attempts++;
        if (storedData.attempts > 3) {
            otpStore.delete(userId);
            logger.warn('Too many OTP attempts', { userId });
            return res.status(400).json({ error: 'Too many attempts' });
        }

        // Verify OTP
        if (storedData.otp !== otp) {
            logger.warn('Invalid OTP attempt', { userId, attempt: storedData.attempts });
            return res.status(400).json({ error: 'Invalid OTP' });
        }

        // OTP is valid
        otpStore.delete(userId);
        logger.info('OTP verified successfully', { userId });
        
        // Notify Zitadel about successful verification
        try {
            await notifyZitadelOTPSuccess(userId);
        } catch (notifyError) {
            logger.error('Failed to notify Zitadel', notifyError);
            // Still return success if OTP was valid
        }
        
        res.json({ success: true, message: 'OTP verified' });

    } catch (error) {
        logger.error('Error in verify-otp:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Notify Zitadel about successful OTP verification
async function notifyZitadelOTPSuccess(userId) {
    try {
        const response = await axios.post(
            `${process.env.ZITADEL_URL}/management/v1/users/${userId}/otp/verify`,
            { verified: true },
            {
                headers: {
                    'Authorization': `Bearer ${process.env.ZITADEL_API_TOKEN}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        return response.data;
    } catch (error) {
        logger.error('Error notifying Zitadel:', error.response?.data || error.message);
        throw error;
    }
}

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        otpCount: otpStore.size
    });
});

// Metrics endpoint
app.get('/metrics', (req, res) => {
    const metrics = {
        timestamp: new Date().toISOString(),
        otpStore: {
            size: otpStore.size,
            entries: []
        }
    };
    
    // Add sanitized OTP entries
    for (const [userId, data] of otpStore.entries()) {
        metrics.otpStore.entries.push({
            userId: userId.substring(0, 8) + '...',
            expiresIn: Math.max(0, data.expiresAt - Date.now()),
            attempts: data.attempts
        });
    }
    
    res.json(metrics);
});

// Error handling middleware
app.use((err, req, res, next) => {
    logger.error('Unhandled error:', err);
    res.status(500).json({ error: 'Internal server error' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    logger.info(`SMS OTP service running on port ${PORT}`);
});