#!/usr/bin/env python3
"""
Zitadel SMS Webhook Example
This webhook receives SMS requests from Zitadel and forwards them to your SMS provider.
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
import requests
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration - set these environment variables
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-webhook-secret')
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'twilio')  # twilio, messagebird, vonage, custom

# Provider configurations
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')

MESSAGEBIRD_ACCESS_KEY = os.getenv('MESSAGEBIRD_ACCESS_KEY')
MESSAGEBIRD_FROM = os.getenv('MESSAGEBIRD_FROM', 'Zitadel')

VONAGE_API_KEY = os.getenv('VONAGE_API_KEY')
VONAGE_API_SECRET = os.getenv('VONAGE_API_SECRET')
VONAGE_FROM = os.getenv('VONAGE_FROM', 'Zitadel')

CUSTOM_SMS_ENDPOINT = os.getenv('CUSTOM_SMS_ENDPOINT')
CUSTOM_SMS_API_KEY = os.getenv('CUSTOM_SMS_API_KEY')


def authenticate(f):
    """Simple authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            if token == WEBHOOK_SECRET:
                return f(*args, **kwargs)
        return jsonify({"success": False, "error": "Unauthorized"}), 401
    return decorated_function


def parse_zitadel_payload(payload):
    """Extract SMS details from Zitadel payload"""
    try:
        phone_number = payload['contextInfo']['recipient']['phoneNumber']
        template_content = payload['templateData']['content']
        args = payload.get('args', {})
        
        # Replace template variables
        message = template_content
        for key, value in args.items():
            message = message.replace(f'{{{{{key}}}}}', str(value))
            message = message.replace(f'{{{{.{key}}}}}', str(value))
        
        return phone_number, message
    except KeyError as e:
        logger.error(f"Error parsing payload: {e}")
        raise ValueError(f"Invalid payload structure: {e}")


def send_via_twilio(phone_number, message):
    """Send SMS via Twilio"""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER]):
        raise ValueError("Twilio credentials not configured")
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    data = {
        'From': TWILIO_FROM_NUMBER,
        'To': phone_number,
        'Body': message
    }
    
    response = requests.post(url, auth=auth, data=data)
    if response.status_code == 201:
        return response.json()['sid']
    else:
        raise Exception(f"Twilio error: {response.text}")


def send_via_messagebird(phone_number, message):
    """Send SMS via MessageBird"""
    if not MESSAGEBIRD_ACCESS_KEY:
        raise ValueError("MessageBird access key not configured")
    
    url = "https://rest.messagebird.com/messages"
    headers = {
        'Authorization': f'AccessKey {MESSAGEBIRD_ACCESS_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'originator': MESSAGEBIRD_FROM,
        'recipients': [phone_number.replace('+', '')],
        'body': message
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 201:
        return response.json()['id']
    else:
        raise Exception(f"MessageBird error: {response.text}")


def send_via_vonage(phone_number, message):
    """Send SMS via Vonage (Nexmo)"""
    if not all([VONAGE_API_KEY, VONAGE_API_SECRET]):
        raise ValueError("Vonage credentials not configured")
    
    url = "https://rest.nexmo.com/sms/json"
    data = {
        'api_key': VONAGE_API_KEY,
        'api_secret': VONAGE_API_SECRET,
        'from': VONAGE_FROM,
        'to': phone_number,
        'text': message
    }
    
    response = requests.post(url, data=data)
    result = response.json()
    if response.status_code == 200 and result['messages'][0]['status'] == '0':
        return result['messages'][0]['message-id']
    else:
        raise Exception(f"Vonage error: {result}")


def send_via_custom(phone_number, message):
    """Send SMS via custom provider"""
    if not CUSTOM_SMS_ENDPOINT:
        raise ValueError("Custom SMS endpoint not configured")
    
    headers = {
        'Content-Type': 'application/json'
    }
    if CUSTOM_SMS_API_KEY:
        headers['Authorization'] = f'Bearer {CUSTOM_SMS_API_KEY}'
    
    data = {
        'to': phone_number,
        'message': message,
        'from': 'Zitadel'
    }
    
    response = requests.post(CUSTOM_SMS_ENDPOINT, headers=headers, json=data)
    if response.status_code == 200:
        return response.json().get('messageId', 'custom-' + str(datetime.now().timestamp()))
    else:
        raise Exception(f"Custom provider error: {response.text}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "provider": SMS_PROVIDER})


@app.route('/send', methods=['POST'])
@authenticate
def send_sms():
    """Main webhook endpoint for Zitadel SMS requests"""
    try:
        # Parse request
        payload = request.get_json()
        logger.info(f"Received SMS request: {json.dumps(payload, indent=2)}")
        
        # Extract SMS details
        phone_number, message = parse_zitadel_payload(payload)
        logger.info(f"Sending SMS to {phone_number}: {message[:50]}...")
        
        # Send via configured provider
        message_id = None
        if SMS_PROVIDER == 'twilio':
            message_id = send_via_twilio(phone_number, message)
        elif SMS_PROVIDER == 'messagebird':
            message_id = send_via_messagebird(phone_number, message)
        elif SMS_PROVIDER == 'vonage':
            message_id = send_via_vonage(phone_number, message)
        elif SMS_PROVIDER == 'custom':
            message_id = send_via_custom(phone_number, message)
        else:
            raise ValueError(f"Unknown SMS provider: {SMS_PROVIDER}")
        
        logger.info(f"SMS sent successfully: {message_id}")
        return jsonify({
            "success": True,
            "messageId": message_id,
            "provider": SMS_PROVIDER
        }), 200
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        return jsonify({"success": False, "error": "Failed to send SMS"}), 500


@app.route('/test', methods=['POST'])
def test_endpoint():
    """Test endpoint for debugging"""
    return jsonify({
        "success": True,
        "message": "Test endpoint working",
        "headers": dict(request.headers),
        "body": request.get_json()
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting SMS webhook server on port {port}")
    logger.info(f"Configured provider: {SMS_PROVIDER}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)