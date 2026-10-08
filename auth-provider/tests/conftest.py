from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from auth_service.config import Settings
from auth_service.presentation.api import create_app


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    app = create_app(
        Settings(
            database_url=f"sqlite:///{tmp_path / 'test.db'}",
            secret_key="test-secret-key-that-is-long-enough-for-tests",
        )
    )
    with TestClient(app) as test_client:
        yield test_client
