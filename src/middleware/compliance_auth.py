# Compliance Authentication Middleware
"""
Authentication middleware for compliance portal endpoints.
Supports both token-based (lite version) and JWT-based (full version) authentication.

Token-based Authentication:
- Used for lite version CCO access
- Tokens embedded in URLs or Authorization headers
- Validates HMAC signatures and expiration

JWT Authentication:
- Used for full version CCO dashboard access
- Standard Bearer token authentication
- Role-based access control
"""

import logging
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.utils import get_authorization_scheme_param

from src.services.token_manager import token_manager, TokenValidationError

logger = logging.getLogger(__name__)

# Security schemes
bearer_scheme = HTTPBearer(auto_error=False)


class ComplianceAuthContext:
    """Authentication context for compliance endpoints"""
    
    def __init__(
        self,
        auth_type: str,  # 'token' or 'jwt'
        token_data: Dict[str, Any],
        content_id: Optional[str] = None,
        cco_email: Optional[str] = None,
        cco_id: Optional[int] = None,
        permissions: Optional[list] = None
    ):
        self.auth_type = auth_type
        self.token_data = token_data
        self.content_id = content_id
        self.cco_email = cco_email
        self.cco_id = cco_id
        self.permissions = permissions or []
        
    def is_token_auth(self) -> bool:
        """Check if using token-based authentication (lite version)"""
        return self.auth_type == 'token'
        
    def is_jwt_auth(self) -> bool:
        """Check if using JWT authentication (full version)"""
        return self.auth_type == 'jwt'
        
    def can_access_content(self, content_id: str) -> bool:
        """Check if authenticated user can access specific content"""
        if self.is_token_auth():
            # Token auth: can only access the specific content in the token
            return str(self.content_id) == str(content_id)
        else:
            # JWT auth: can access any content (full version)
            return True
            
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions


async def extract_review_token_from_request(request: Request) -> Optional[str]:
    """
    Extract review token from request.
    Checks multiple locations: URL parameter, Authorization header.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Review token if found, None otherwise
    """
    # 1. Check URL path parameter (for /review/{token} endpoints)
    if hasattr(request, 'path_params') and 'token' in request.path_params:
        token = request.path_params['token']
        if token:
            logger.debug("Found review token in URL path parameter")
            return token
    
    # 2. Check query parameter
    token = request.query_params.get('token')
    if token:
        logger.debug("Found review token in query parameter")
        return token
    
    # 3. Check Authorization header (Bearer token)
    authorization: str = request.headers.get("Authorization")
    if authorization:
        scheme, credentials = get_authorization_scheme_param(authorization)
        if scheme.lower() == "bearer" and credentials:
            # Could be either a review token or JWT - let caller determine
            logger.debug("Found token in Authorization header")
            return credentials
    
    return None


async def validate_review_token_auth(
    request: Request,
    require_content_id: Optional[str] = None
) -> ComplianceAuthContext:
    """
    Validate review token authentication.
    
    Args:
        request: FastAPI request object
        require_content_id: If provided, token must be for this specific content
        
    Returns:
        Authentication context
        
    Raises:
        HTTPException: If authentication fails
    """
    # Extract token from request
    token = await extract_review_token_from_request(request)
    
    if not token:
        logger.warning("No review token found in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Review token required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Validate token
        token_data = token_manager.validate_review_token(
            token=token,
            require_content_id=require_content_id
        )
        
        # Create authentication context
        auth_context = ComplianceAuthContext(
            auth_type='token',
            token_data=token_data,
            content_id=token_data.get('content_id'),
            cco_email=token_data.get('cco_email'),
            permissions=['review_content']  # Basic permission for token auth
        )
        
        logger.info(
            f"Successful token authentication for content_id={auth_context.content_id}, "
            f"cco_email={auth_context.cco_email}"
        )
        
        return auth_context
        
    except TokenValidationError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid review token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


# Dependency functions for FastAPI endpoints

async def require_review_token_auth(request: Request) -> ComplianceAuthContext:
    """
    Dependency that requires valid review token authentication.
    Use this for endpoints that accept any valid review token.
    
    Usage:
        @router.get("/some-endpoint")
        async def endpoint(auth: ComplianceAuthContext = Depends(require_review_token_auth)):
            # Access auth.content_id, auth.cco_email, etc.
    """
    return await validate_review_token_auth(request)


def require_review_token_for_content(content_id: str):
    """
    Dependency factory that requires a review token for specific content.
    Use this for endpoints that should only allow access to specific content.
    
    Args:
        content_id: Required content ID
        
    Returns:
        Dependency function
        
    Usage:
        @router.get("/content/{content_id}/review")
        async def review_content(
            content_id: str,
            auth: ComplianceAuthContext = Depends(require_review_token_for_content(content_id))
        ):
            # Token is guaranteed to be for this specific content
    """
    async def _auth_dependency(request: Request) -> ComplianceAuthContext:
        return await validate_review_token_auth(request, require_content_id=content_id)
    
    return _auth_dependency


# Utility functions for manual token validation

async def validate_token_from_path_param(token: str) -> ComplianceAuthContext:
    """
    Validate a token that comes from a path parameter.
    Useful for endpoints with {token} in the URL path.
    
    Args:
        token: Token from URL path
        
    Returns:
        Authentication context
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        token_data = token_manager.validate_review_token(token)
        
        return ComplianceAuthContext(
            auth_type='token',
            token_data=token_data,
            content_id=token_data.get('content_id'),
            cco_email=token_data.get('cco_email'),
            permissions=['review_content']
        )
        
    except TokenValidationError as e:
        logger.warning(f"Path token validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid review token: {str(e)}"
        )


def create_token_validator_dependency(require_content_access: bool = True):
    """
    Create a custom token validator dependency.
    
    Args:
        require_content_access: If True, validates content access permissions
        
    Returns:
        FastAPI dependency function
        
    Usage:
        custom_auth = create_token_validator_dependency(require_content_access=False)
        
        @router.get("/endpoint")
        async def endpoint(auth: ComplianceAuthContext = Depends(custom_auth)):
            pass
    """
    async def _validator(request: Request) -> ComplianceAuthContext:
        auth_context = await validate_review_token_auth(request)
        
        if require_content_access and not auth_context.content_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token does not provide content access"
            )
            
        return auth_context
    
    return _validator


# Error handling utilities

def create_auth_error_response(detail: str, status_code: int = status.HTTP_401_UNAUTHORIZED) -> HTTPException:
    """
    Create a standardized authentication error response.
    
    Args:
        detail: Error message
        status_code: HTTP status code
        
    Returns:
        HTTPException with appropriate headers
    """
    return HTTPException(
        status_code=status_code,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"}
    )


def log_auth_attempt(
    request: Request,
    success: bool,
    auth_type: str,
    details: Optional[Dict[str, Any]] = None
):
    """
    Log authentication attempt for audit trail.
    
    Args:
        request: FastAPI request object
        success: Whether authentication succeeded
        auth_type: Type of authentication used
        details: Additional details to log
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    log_data = {
        "event": "auth_attempt",
        "success": success,
        "auth_type": auth_type,
        "client_ip": client_ip,
        "user_agent": user_agent,
        "path": str(request.url.path),
        "method": request.method
    }
    
    if details:
        log_data.update(details)
    
    if success:
        logger.info(f"Authentication successful: {log_data}")
    else:
        logger.warning(f"Authentication failed: {log_data}")
