## Configure ENV variables for the application

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # CORS Configuration
    ALLOW_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    ALLOW_METHODS: str = "POST,GET,OPTIONS"
    ALLOW_HEADERS: str = "*"
    
    # Entra ID (Azure AD) Configuration for Client Credentials Flow
    ENABLE_AUTH: bool = False  # Set to True to enable authentication
    AUTH_PROVIDER_URL: Optional[str] = None
    AZURE_TENANT_ID: Optional[str] = None
    AZURE_CLIENT_ID: Optional[str] = None  # Application (client) ID
    AZURE_CLIENT_SECRET: Optional[str] = None
    # Expected audience in the token (usually api://<client-id> or Application ID URI)
    AZURE_AUDIENCE: Optional[str] = None
    # Issuer format: https://login.microsoftonline.com/{tenant_id}/v2.0
    AZURE_ISSUER: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding='utf-8', 
        extra='ignore'
    )

    @property
    def jwks_uri(self) -> Optional[str]:
        """Generate JWKS URI from tenant ID - v1 endpoint for sts.windows.net tokens"""
        if self.AZURE_TENANT_ID:
            return f"https://login.microsoftonline.com/{self.AZURE_TENANT_ID}/discovery/keys"
        return None

    @property
    def token_endpoint(self) -> Optional[str]:
        """Generate token endpoint from tenant ID"""
        if self.AZURE_TENANT_ID:
            return f"https://login.microsoftonline.com/{self.AZURE_TENANT_ID}/oauth2/v2.0/token"
        return None


settings = Settings()