from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from dice_applet.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Async test client with the app's startup/shutdown lifespan applied."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
            yield ac
