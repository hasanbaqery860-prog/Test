"""
Zitadel OAuth2 Backend for Open edX
Place this file in: /edx/app/edxapp/edx-platform/common/djangoapps/third_party_auth/

Usage:
1. Add to AUTHENTICATION_BACKENDS in lms.env.json
2. Configure provider in Django Admin
"""

from social_core.backends.open_id_connect import OpenIdConnectAuth
from social_core.exceptions import AuthException
import logging

logger = logging.getLogger(__name__)


class ZitadelOAuth2(OpenIdConnectAuth):
    """
    Zitadel OAuth2 authentication backend for Open edX
    """
    name = 'zitadel'
    
    # Zitadel endpoints (update with your domain)
    OIDC_ENDPOINT = 'https://auth.yourdomain.com'
    
    # Default scopes
    DEFAULT_SCOPE = ['openid', 'profile', 'email', 'phone']
    
    # Extra data to store
    EXTRA_DATA = [
        ('sub', 'id'),
        ('email', 'email'),
        ('name', 'full_name'),
        ('given_name', 'first_name'),
        ('family_name', 'last_name'),
        ('preferred_username', 'username'),
        ('phone_number', 'phone'),
        ('phone_number_verified', 'phone_verified'),
        ('locale', 'locale'),
        ('picture', 'profile_picture'),
    ]
    
    def oidc_config(self):
        """
        Get OIDC configuration from Zitadel
        """
        return self.get_json(
            f'{self.OIDC_ENDPOINT}/.well-known/openid-configuration'
        )
    
    def get_user_details(self, response):
        """
        Extract user details from Zitadel response
        """
        username = response.get('preferred_username', '')
        email = response.get('email', '')
        fullname = response.get('name', '')
        first_name = response.get('given_name', '')
        last_name = response.get('family_name', '')
        
        # Handle missing username
        if not username and email:
            username = email.split('@')[0]
        
        return {
            'username': username,
            'email': email,
            'fullname': fullname,
            'first_name': first_name,
            'last_name': last_name,
        }
    
    def user_data(self, access_token, *args, **kwargs):
        """
        Get user data from Zitadel userinfo endpoint
        """
        return self.get_json(
            self.userinfo_url(),
            headers={'Authorization': f'Bearer {access_token}'}
        )
    
    def refresh_token(self, refresh_token, *args, **kwargs):
        """
        Refresh access token using refresh token
        """
        params = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': self.setting('KEY'),
            'client_secret': self.setting('SECRET'),
        }
        
        response = self.request_access_token(
            self.access_token_url(),
            data=params,
            headers=self.auth_headers(),
            method='POST'
        )
        
        return response.get('access_token'), response.get('refresh_token')
    
    def auth_html(self):
        """
        Custom HTML for login button (optional)
        """
        return '''
        <button class="btn-zitadel" type="submit">
            <img src="/static/images/zitadel-logo.svg" alt="Zitadel" />
            <span>Sign in with Zitadel</span>
        </button>
        '''
    
    def get_user_id(self, details, response):
        """
        Get unique user ID from Zitadel response
        """
        return response.get('sub')
    
    def auth_allowed(self, response, details):
        """
        Check if authentication is allowed
        """
        # Verify email is present and verified
        email = response.get('email')
        email_verified = response.get('email_verified', False)
        
        if not email:
            logger.error('Zitadel auth failed: No email provided')
            raise AuthException('Email is required for authentication')
        
        if not email_verified:
            logger.warning(f'Zitadel auth: Unverified email for {email}')
            # You may want to allow unverified emails depending on your policy
            # raise AuthException('Email must be verified')
        
        # Check if SMS OTP was verified (if required)
        if response.get('sms_otp_required') and not response.get('sms_otp_verified'):
            logger.error(f'Zitadel auth failed: SMS OTP required but not verified for {email}')
            raise AuthException('SMS verification required')
        
        return True
    
    def pipeline(self, request, pipeline, *args, **kwargs):
        """
        Custom pipeline processing
        """
        # Log authentication attempt
        user_email = kwargs.get('details', {}).get('email', 'unknown')
        logger.info(f'Zitadel authentication attempt for: {user_email}')
        
        return super().pipeline(request, pipeline, *args, **kwargs)


# Additional pipeline functions for Open edX integration

def ensure_user_information(backend, details, response, user=None, *args, **kwargs):
    """
    Pipeline function to ensure user information is complete
    """
    if user:
        # Update phone number if provided
        phone = response.get('phone_number')
        if phone and hasattr(user, 'profile'):
            user.profile.phone_number = phone
            user.profile.save()
        
        # Update locale if provided
        locale = response.get('locale')
        if locale:
            user.preferences.language = locale
            user.preferences.save()
    
    return {'user': user}


def track_login_analytics(backend, details, response, user=None, *args, **kwargs):
    """
    Pipeline function to track authentication analytics
    """
    if user:
        # Log successful authentication
        logger.info(f'Successful Zitadel authentication for user: {user.username}')
        
        # Track event (integrate with your analytics)
        # track_event('user.authenticated', {
        #     'provider': 'zitadel',
        #     'user_id': user.id,
        #     'email': user.email,
        # })
    
    return {'user': user}