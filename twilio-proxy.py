#!/usr/bin/env python3
"""
Twilio API Proxy for Zitadel v2.42.0
This proxy intercepts Twilio API calls from Zitadel and forwards them to other SMS providers.
"""

import os
import logging
import base64
from datetime import datetime
from flask import Flask, request, Response, jsonify
import requests
from urllib.parse import parse_qs
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
SMS_PROVIDER = os.getenv('SMS_PROVIDER', 'messagebird')  # messagebird, vonage, custom
AUTH_REQUIRED = os.getenv('AUTH_REQUIRED', 'true').lower() == 'true'

# Expected Twilio credentials from Zitadel (for authentication)
EXPECTED_ACCOUNT_SID = os.getenv('EXPECTED_ACCOUNT_SID', 'dummy-account-sid')
EXPECTED_AUTH_TOKEN = os.getenv('EXPECTED_AUTH_TOKEN', 'dummy-auth-token')

# Actual SMS provider configurations
MESSAGEBIRD_ACCESS_KEY = os.getenv('MESSAGEBIRD_ACCESS_KEY')
MESSAGEBIRD_FROM = os.getenv('MESSAGEBIRD_FROM', 'Zitadel')

VONAGE_API_KEY = os.getenv('VONAGE_API_KEY')
VONAGE_API_SECRET = os.getenv('VONAGE_API_SECRET')
VONAGE_FROM = os.getenv('VONAGE_FROM', 'Zitadel')

CUSTOM_SMS_ENDPOINT = os.getenv('CUSTOM_SMS_ENDPOINT')
CUSTOM_SMS_API_KEY = os.getenv('CUSTOM_SMS_API_KEY')


def verify_twilio_auth():
    """Verify Twilio-style basic authentication"""
    if not AUTH_REQUIRED:
        return True
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Basic '):
        return False
    
    try:
        credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
        account_sid, auth_token = credentials.split(':', 1)
        return (account_sid == EXPECTED_ACCOUNT_SID and 
                auth_token == EXPECTED_AUTH_TOKEN)
    except Exception as e:
        logger.error(f"Auth verification error: {e}")
        return False


def create_twilio_response(sid, status='queued'):
    """Create a Twilio-compatible XML response"""
    root = ET.Element('TwilioResponse')
    message = ET.SubElement(root, 'Message')
    
    # Add standard Twilio response fields
    ET.SubElement(message, 'Sid').text = sid
    ET.SubElement(message, 'DateCreated').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    ET.SubElement(message, 'DateUpdated').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')
    ET.SubElement(message, 'AccountSid').text = EXPECTED_ACCOUNT_SID
    ET.SubElement(message, 'Status').text = status
    ET.SubElement(message, 'Direction').text = 'outbound-api'
    ET.SubElement(message, 'ApiVersion').text = '2010-04-01'
    ET.SubElement(message, 'Price').text = ''
    ET.SubElement(message, 'PriceUnit').text = 'USD'
    
    return ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')


def send_via_messagebird(to, body, from_number=None):
    """Forward SMS to MessageBird"""
    if not MESSAGEBIRD_ACCESS_KEY:
        raise ValueError("MessageBird access key not configured")
    
    response = requests.post(
        'https://rest.messagebird.com/messages',
        headers={
            'Authorization': f'AccessKey {MESSAGEBIRD_ACCESS_KEY}',
            'Content-Type': 'application/json'
        },
        json={
            'originator': from_number or MESSAGEBIRD_FROM,
            'recipients': [to.replace('+', '')],
            'body': body
        }
    )
    
    if response.status_code == 201:
        return response.json().get('id', 'MB' + str(datetime.now().timestamp()))
    else:
        logger.error(f"MessageBird error: {response.text}")
        response.raise_for_status()


def send_via_vonage(to, body, from_number=None):
    """Forward SMS to Vonage (Nexmo)"""
    if not all([VONAGE_API_KEY, VONAGE_API_SECRET]):
        raise ValueError("Vonage credentials not configured")
    
    response = requests.post(
        'https://rest.nexmo.com/sms/json',
        data={
            'api_key': VONAGE_API_KEY,
            'api_secret': VONAGE_API_SECRET,
            'from': from_number or VONAGE_FROM,
            'to': to,
            'text': body
        }
    )
    
    result = response.json()
    if response.status_code == 200 and result['messages'][0]['status'] == '0':
        return result['messages'][0]['message-id']
    else:
        logger.error(f"Vonage error: {result}")
        raise Exception(f"Vonage error: {result}")


def send_via_custom(to, body, from_number=None):
    """Forward SMS to custom provider"""
    if not CUSTOM_SMS_ENDPOINT:
        raise ValueError("Custom SMS endpoint not configured")
    
    headers = {'Content-Type': 'application/json'}
    if CUSTOM_SMS_API_KEY:
        headers['Authorization'] = f'Bearer {CUSTOM_SMS_API_KEY}'
    
    response = requests.post(
        CUSTOM_SMS_ENDPOINT,
        headers=headers,
        json={
            'to': to,
            'message': body,
            'from': from_number or 'Zitadel'
        }
    )
    
    if response.status_code == 200:
        return response.json().get('messageId', 'CUSTOM' + str(datetime.now().timestamp()))
    else:
        logger.error(f"Custom provider error: {response.text}")
        response.raise_for_status()


@app.route('/2010-04-01/Accounts/<account_sid>/Messages.json', methods=['POST'])
@app.route('/2010-04-01/Accounts/<account_sid>/Messages', methods=['POST'])
def handle_twilio_sms(account_sid):
    """Main endpoint that mimics Twilio's SMS API"""
    
    # Verify authentication
    if not verify_twilio_auth():
        return Response('Unauthorized', 401)
    
    try:
        # Parse form data (Twilio uses form-encoded data)
        if request.content_type == 'application/x-www-form-urlencoded':
            data = request.form
        else:
            data = parse_qs(request.get_data(as_text=True))
            data = {k: v[0] if isinstance(v, list) else v for k, v in data.items()}
        
        to_number = data.get('To', '')
        from_number = data.get('From', '')
        body = data.get('Body', '')
        
        logger.info(f"Received SMS request: To={to_number}, From={from_number}, Body={body[:50]}...")
        
        # Forward to actual SMS provider
        if SMS_PROVIDER == 'messagebird':
            message_id = send_via_messagebird(to_number, body, from_number)
        elif SMS_PROVIDER == 'vonage':
            message_id = send_via_vonage(to_number, body, from_number)
        elif SMS_PROVIDER == 'custom':
            message_id = send_via_custom(to_number, body, from_number)
        else:
            raise ValueError(f"Unknown SMS provider: {SMS_PROVIDER}")
        
        logger.info(f"SMS sent successfully via {SMS_PROVIDER}: {message_id}")
        
        # Generate Twilio-compatible response
        sid = f"SM{message_id[:32].ljust(32, '0')}"
        xml_response = create_twilio_response(sid, 'queued')
        
        return Response(
            '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_response,
            mimetype='application/xml'
        )
        
    except Exception as e:
        logger.error(f"Error processing SMS: {e}")
        
        # Return Twilio-style error response
        root = ET.Element('TwilioResponse')
        error = ET.SubElement(root, 'RestException')
        ET.SubElement(error, 'Code').text = '21211'
        ET.SubElement(error, 'Message').text = str(e)
        ET.SubElement(error, 'Status').text = '400'
        
        error_xml = ET.tostring(root, encoding='utf-8', method='xml').decode('utf-8')
        return Response(
            '<?xml version="1.0" encoding="UTF-8"?>\n' + error_xml,
            status=400,
            mimetype='application/xml'
        )


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "provider": SMS_PROVIDER,
        "proxy": "twilio-api"
    })


@app.route('/', methods=['GET'])
def root():
    """Root endpoint to mimic Twilio API"""
    return jsonify({
        "api_version": "2010-04-01",
        "proxy": "twilio-proxy",
        "actual_provider": SMS_PROVIDER
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    ssl_cert = os.getenv('SSL_CERT')
    ssl_key = os.getenv('SSL_KEY')
    
    logger.info(f"Starting Twilio proxy server on port {port}")
    logger.info(f"Proxying to SMS provider: {SMS_PROVIDER}")
    logger.info(f"Authentication required: {AUTH_REQUIRED}")
    
    if ssl_cert and ssl_key:
        logger.info("Running with SSL")
        app.run(host='0.0.0.0', port=port, ssl_context=(ssl_cert, ssl_key))
    else:
        logger.warning("Running without SSL - use only for development!")
        app.run(host='0.0.0.0', port=port)