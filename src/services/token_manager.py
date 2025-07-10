# Token Manager Service
"""
Cryptographically secure token generation and validation for compliance portal.
Implements HMAC-based tokens with content ID, CCO email, and timestamp.

Security Features:
- HMAC-SHA256 signatures for tamper detection
- URL-safe base64 encoding
- Optional expiration times
- Audit logging for security tracking
"""

import hmac
import hashlib
import json
import time
import secrets
import base64
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import quote, unquote

from config.settings import settings

logger = logging.getLogger(__name__)


class TokenValidationError(Exception):
    """Raised when token validation fails"""
    pass


class TokenManager:
    """Manages secure token generation and validation for compliance reviews"""
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize token manager with secret key.
        
        Args:
            secret_key: Secret key for HMAC signing. If None, uses settings.
        """
        # Use provided secret or fall back to a derived key from anthropic_api_key
        self.secret_key = secret_key or self._get_secret_key()
        self.algorithm = 'HS256'
        
    def _get_secret_key(self) -> str:
        """
        Get secret key for token signing.
        In production, this should be a dedicated secret.
        """
        # For MVP, derive from existing API key
        # In production, use a dedicated TOKEN_SECRET_KEY environment variable
        base_secret = getattr(settings, 'token_secret_key', None)
        if base_secret:
            return base_secret
            
        # Fallback: derive from anthropic key for development
        return hashlib.sha256(f"compliance_tokens_{settings.anthropic_api_key}".encode()).hexdigest()
    
    def generate_review_token(
        self,
        content_id: str,
        cco_email: str,
        expires_hours: Optional[int] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a secure review token for content access.
        
        Args:
            content_id: ID of content to be reviewed
            cco_email: Email of CCO who will review
            expires_hours: Hours until token expires (None = no expiration)
            additional_data: Optional additional data to include in token
            
        Returns:
            URL-safe token string
            
        Raises:
            ValueError: If required parameters are invalid
        """
        if not content_id or not cco_email:
            raise ValueError("content_id and cco_email are required")
            
        # Create token payload
        now = int(time.time())
        payload = {
            'content_id': str(content_id),
            'cco_email': cco_email.lower().strip(),
            'issued_at': now,
            'nonce': secrets.token_hex(16),  # Random nonce for uniqueness
            'version': '1'  # Token format version
        }
        
        # Add expiration if specified
        if expires_hours is not None:
            payload['expires_at'] = now + (expires_hours * 3600)
            
        # Add any additional data
        if additional_data:
            payload['additional'] = additional_data
            
        # Create token
        token = self._create_signed_token(payload)
        
        # Log token generation for audit trail
        logger.info(
            f"Generated review token for content_id={content_id}, "
            f"cco_email={cco_email}, expires_hours={expires_hours}"
        )
        
        return token
    
    def validate_review_token(
        self, 
        token: str,
        require_content_id: Optional[str] = None,
        require_cco_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate and decode a review token.
        
        Args:
            token: Token to validate
            require_content_id: If provided, token must match this content ID
            require_cco_email: If provided, token must match this CCO email
            
        Returns:
            Decoded token payload
            
        Raises:
            TokenValidationError: If token is invalid, expired, or doesn't match requirements
        """
        try:
            # Decode and verify token
            payload = self._verify_signed_token(token)
            
            # Check expiration
            if 'expires_at' in payload:
                if time.time() > payload['expires_at']:
                    raise TokenValidationError("Token has expired")
                    
            # Check required content ID
            if require_content_id and payload.get('content_id') != str(require_content_id):
                raise TokenValidationError("Token content ID mismatch")
                
            # Check required CCO email (case-insensitive)
            if require_cco_email:
                token_email = payload.get('cco_email', '').lower().strip()
                required_email = require_cco_email.lower().strip()
                if token_email != required_email:
                    raise TokenValidationError("Token CCO email mismatch")
                    
            # Log successful validation
            logger.info(
                f"Successfully validated token for content_id={payload.get('content_id')}, "
                f"cco_email={payload.get('cco_email')}"
            )
            
            return payload
            
        except json.JSONDecodeError:
            raise TokenValidationError("Invalid token format")
        except Exception as e:
            if isinstance(e, TokenValidationError):
                raise
            logger.error(f"Token validation error: {str(e)}")
            raise TokenValidationError(f"Token validation failed: {str(e)}")
    
    def _create_signed_token(self, payload: Dict[str, Any]) -> str:
        """
        Create a signed token from payload.
        
        Args:
            payload: Data to encode in token
            
        Returns:
            Signed token string
        """
        # Convert payload to JSON
        payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        
        # Encode payload as base64
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip('=')
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key.encode(),
            payload_b64.encode(),
            hashlib.sha256
        ).digest()
        
        # Encode signature as base64
        signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
        
        # Combine payload and signature
        token = f"{payload_b64}.{signature_b64}"
        
        return token
    
    def _verify_signed_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a signed token.
        
        Args:
            token: Token to verify
            
        Returns:
            Decoded payload
            
        Raises:
            TokenValidationError: If signature is invalid or token is malformed
        """
        try:
            # Split token into payload and signature
            parts = token.split('.')
            if len(parts) != 2:
                raise TokenValidationError("Invalid token format")
                
            payload_b64, signature_b64 = parts
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload_b64.encode(),
                hashlib.sha256
            ).digest()
            
            # Decode provided signature
            # Add padding if needed
            signature_b64_padded = signature_b64 + '=' * (4 - len(signature_b64) % 4)
            provided_signature = base64.urlsafe_b64decode(signature_b64_padded)
            
            # Compare signatures using constant-time comparison
            if not hmac.compare_digest(expected_signature, provided_signature):
                raise TokenValidationError("Invalid token signature")
                
            # Decode payload
            # Add padding if needed
            payload_b64_padded = payload_b64 + '=' * (4 - len(payload_b64) % 4)
            payload_json = base64.urlsafe_b64decode(payload_b64_padded).decode()
            
            # Parse JSON payload
            payload = json.loads(payload_json)
            
            return payload
            
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            raise TokenValidationError(f"Token decoding failed: {str(e)}")
    
    def get_token_info(self, token: str) -> Dict[str, Any]:
        """
        Get information about a token without full validation.
        Useful for debugging and logging.
        
        Args:
            token: Token to inspect
            
        Returns:
            Token information including validity status
        """
        try:
            payload = self._verify_signed_token(token)
            
            # Check if expired
            is_expired = False
            if 'expires_at' in payload:
                is_expired = time.time() > payload['expires_at']
                
            return {
                'valid_signature': True,
                'expired': is_expired,
                'content_id': payload.get('content_id'),
                'cco_email': payload.get('cco_email'),
                'issued_at': payload.get('issued_at'),
                'expires_at': payload.get('expires_at'),
                'age_seconds': int(time.time()) - payload.get('issued_at', 0)
            }
            
        except TokenValidationError:
            return {
                'valid_signature': False,
                'expired': None,
                'content_id': None,
                'cco_email': None,
                'issued_at': None,
                'expires_at': None,
                'age_seconds': None
            }
    
    def create_review_url(
        self, 
        token: str, 
        base_url: str = "https://compliance.fiducia.ai"
    ) -> str:
        """
        Create a complete review URL with token.
        
        Args:
            token: Review token
            base_url: Base URL for compliance portal
            
        Returns:
            Complete review URL
        """
        # URL-encode the token for safety
        encoded_token = quote(token, safe='')
        return f"{base_url}/review/{encoded_token}"


# Global token manager instance
token_manager = TokenManager()


# Convenience functions for common operations
def generate_review_token(
    content_id: str,
    cco_email: str,
    expires_hours: Optional[int] = None
) -> str:
    """Generate a review token using the global token manager"""
    return token_manager.generate_review_token(content_id, cco_email, expires_hours)


def validate_review_token(token: str) -> Dict[str, Any]:
    """Validate a review token using the global token manager"""
    return token_manager.validate_review_token(token)


def get_token_info(token: str) -> Dict[str, Any]:
    """Get token information using the global token manager"""
    return token_manager.get_token_info(token)
