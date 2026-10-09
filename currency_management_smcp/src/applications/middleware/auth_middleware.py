"""
Middleware de autenticación para Entra ID (Azure AD) Client Credentials Flow
"""
import logging
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import jwt
from jwt.exceptions import PyJWTError as JWTError, ExpiredSignatureError, InvalidAudienceError, InvalidIssuerError
from jwt.algorithms import RSAAlgorithm
import httpx

from src.applications.config.config import settings
import contextvars
logger = logging.getLogger(__name__)

# ContextVar para compartir el usuario autenticado a través del contexto de la petición
user_ctx = contextvars.ContextVar("user", default=None)

class EntraIDAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware para validar tokens JWT de Entra ID (Azure AD)
    usando Client Credentials Flow
    """
    
    def __init__(
        self,
        app,
        enabled: bool = True,
        auth_provider_url: Optional[str] = None,
    ):
        super().__init__(app)
        self.enabled = enabled
        self.auth_provider_url = auth_provider_url
        self._jwks_cache: Optional[dict] = None
        
        if self.enabled:
            logger.info("✓ Entra ID Authentication Middleware ENABLED")
            logger.info(f"  Tenant ID: {settings.AZURE_TENANT_ID}")
            logger.info(f"  Expected Audience: {settings.AZURE_AUDIENCE}")
            logger.info(f"  JWKS URI: {settings.jwks_uri}")
        else:
            logger.warning("⚠ Authentication is DISABLED (development mode)")
      
    async def dispatch(self, request: Request, call_next):
        """Process each request"""
        
        # Si la autenticación está deshabilitada, permitir todas las peticiones
        if not self.enabled:
            return await call_next(request)
        
        # Rutas públicas que no requieren autenticación
        public_paths = ["/v1/api/health", "/v1/health/readiness", "/v1/health/liveliness", 
                       "/v1/health/startup", "/docs", "/redoc", "/openapi.json"]
        if request.url.path in public_paths:
            return await call_next(request)
        
        # Obtener el token del header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning(f"Missing Authorization header for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing Authorization header"}
            )
        
        # Validar formato del header
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                raise ValueError("Invalid authentication scheme")
        except ValueError:
            logger.warning(f"Invalid Authorization header format for {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid Authorization header format. Expected: Bearer <token>"}
            )
        
        # Validar el token
        try:
            if self.auth_provider_url:
                payload = await self._validate_with_auth_provider(token)
            else:
                payload = await self._validate_token(token)
            # Agregar información del token al request state para usarla en los handlers
            request.state.user = payload
            request.state.token = token
            # Guardar usuario en contextvar para acceso en tools/resources/prompts
            context_token = user_ctx.set(payload)
            logger.debug(f"✓ Token validated for client: {payload.get('azp', 'unknown')}")
        except JWTError as e:
            logger.error(f"JWT validation error: {str(e)}")
            return JSONResponse(
                status_code=401,
                content={"detail": f"Invalid token: {str(e)}"}
            )
        except RuntimeError as e:
            logger.error("Authentication service unavailable: %s", e)
            return JSONResponse(
                status_code=503,
                content={"detail": "Authentication service is unavailable."},
            )
        except Exception as e:
            logger.error(f"Unexpected error validating token: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error during authentication"}
            )
        
        try:
            return await call_next(request)
        finally:
            user_ctx.reset(context_token)

    async def _validate_with_auth_provider(self, token: str) -> dict:
        """Validate the user's access token with the authentication service."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    self.auth_provider_url,
                    headers={"Authorization": f"Bearer {token}"},
                )
        except httpx.RequestError as error:
            logger.error("Auth provider request failed: %s", error)
            raise RuntimeError("Authentication provider is unavailable.") from error

        if response.status_code == 401:
            raise JWTError("Invalid or expired access token")
        if response.status_code != 200:
            raise RuntimeError(
                f"Authentication provider returned HTTP {response.status_code}."
            )

        try:
            result = response.json()
        except ValueError as error:
            raise RuntimeError("Authentication provider returned invalid JSON.") from error

        user = result.get("user") if isinstance(result, dict) else None
        if not isinstance(result, dict) or result.get("valid") is not True:
            raise JWTError("Invalid or expired access token")
        if not isinstance(user, dict):
            raise RuntimeError("Authentication provider returned an invalid user.")
        return user
    
    async def _validate_token(self, token: str) -> dict:
        """
        Valida el token JWT usando las claves públicas de Entra ID
        """
        # Obtener las claves públicas (JWKS)
        if not self._jwks_cache:
            self._jwks_cache = await self._fetch_jwks()
        
        # Decodificar el header del token para obtener el 'kid'
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        
        if not kid:
            raise JWTError("Token missing 'kid' in header")
        
        # Buscar la clave pública correspondiente
        rsa_key = None
        for key in self._jwks_cache.get("keys", []):
            if key["kid"] == kid:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break
        
        if not rsa_key:
            # Intentar refrescar el cache de JWKS
            logger.info("Key not found in cache, refreshing JWKS...")
            self._jwks_cache = await self._fetch_jwks()
            for key in self._jwks_cache.get("keys", []):
                if key["kid"] == kid:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
                    break
        
        if not rsa_key:
            raise JWTError(f"Public key not found for kid: {kid}")
        
        # Convertir JWK a PEM
        try:
            public_key = RSAAlgorithm.from_jwk(rsa_key)
        except Exception as e:
            raise JWTError(f"Failed to convert JWK to PEM: {str(e)}")
        
        # Validar el token
        try:
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=settings.AZURE_AUDIENCE,
                issuer=settings.AZURE_ISSUER,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
            return payload
        except ExpiredSignatureError:
            raise JWTError("Token has expired")
        except (InvalidAudienceError, InvalidIssuerError) as e:
            raise JWTError(f"Invalid token claims: {str(e)}")
        except Exception as e:
            raise JWTError(f"Token validation failed: {str(e)}")
    
    async def _fetch_jwks(self) -> dict:
        """
        Obtiene las claves públicas (JWKS) de Entra ID
        """
        if not settings.jwks_uri:
            raise ValueError("JWKS URI not configured")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(settings.jwks_uri, timeout=10.0)
                response.raise_for_status()
                jwks = response.json()
                logger.info(f"✓ JWKS fetched successfully from {settings.jwks_uri}")
                return jwks
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch JWKS: {str(e)}")
                raise Exception(f"Failed to fetch JWKS from {settings.jwks_uri}: {str(e)}")
