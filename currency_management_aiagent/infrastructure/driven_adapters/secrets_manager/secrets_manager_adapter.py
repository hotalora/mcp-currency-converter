import json
import logging
from typing import Any
from aiobotocore.session import get_session
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class SecretsManagerAdapter:
    """Adapter for AWS Secrets Manager operations."""

    def __init__(self, aws_config: dict):
        self._session = get_session()
        self.aws_config = aws_config
        self._cache_secrets: dict = {}

    async def get_secret(self,
                         secret_name: str,
                         use_cache: bool = True) -> dict[str, Any]:
        """Retrieve a secret from AWS Secrets Manager.

        Args:
            secret_name: Name of the secret to retrieve.
            use_cache: Whether to use cached secret if available.

        Returns:
            Dictionary containing the secret values.
        """
        if use_cache and secret_name in self._cache_secrets:
            logger.info("Secret %s retrieved from cache", secret_name)
            return self._cache_secrets[secret_name]
        async with self._session.create_client("secretsmanager",
                                               **self.aws_config) as client:
            try:
                logger.info("Retrieving secret: %s", secret_name)
                response = await client.get_secret_value(
                    SecretId=secret_name
                )
                if "SecretString" in response:
                    secret = response["SecretString"]
                    self._cache_secrets[secret_name] = json.loads(secret)
                    return self._cache_secrets[secret_name]
                raise ValueError("SecretString not found in response")
            except (ClientError, BotoCoreError, json.JSONDecodeError) as e:
                logger.error("Error retrieving secret name %s: %s",
                             secret_name, e)
                raise e
