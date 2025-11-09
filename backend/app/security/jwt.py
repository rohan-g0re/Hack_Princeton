"""
Supabase JWT Authentication
Verifies JWT tokens from Supabase Auth and extracts user_id
"""
import jwt
import requests
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import lru_cache
from typing import Dict
from app.config import settings

security = HTTPBearer()


@lru_cache(maxsize=1)
def get_jwks() -> Dict:
    """
    Fetch JWKS (JSON Web Key Set) from Supabase.
    Cached to avoid repeated API calls (cache expires when process restarts).
    """
    jwks_url = f"{settings.supabase_url}/auth/v1/jwks"
    try:
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Unable to fetch JWKS: {str(e)}"
        )


def verify_token(token: str) -> Dict:
    """
    Verify Supabase JWT token and return decoded payload.
    
    Raises:
        HTTPException: If token is invalid, expired, or verification fails
    
    Returns:
        Dict: Decoded token payload containing user info
    """
    try:
        # Decode without verification first to get kid (key ID)
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        # Get JWKS
        jwks = get_jwks()
        
        # Find matching key
        key = None
        for jwk in jwks.get("keys", []):
            if jwk.get("kid") == kid:
                # Convert JWK to RSA key
                key = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)
                break
        
        if not key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no matching key"
            )
        
        # Verify and decode token
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience="authenticated",
            options={"verify_exp": True}
        )
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    FastAPI dependency: Extract and verify user_id from Bearer token.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user_id: str = Depends(get_current_user_id)):
            return {"user_id": user_id}
    
    Raises:
        HTTPException: If authentication fails
    
    Returns:
        str: User ID (UUID) from token 'sub' claim
    """
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing sub claim"
        )
    
    return user_id

