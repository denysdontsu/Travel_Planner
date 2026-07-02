import asyncio
import httpx
from fastapi import HTTPException, status
from app.core.config import settings

# In-memory cash for optimization
_place_existence_cache = {}


async def check_place_exists(external_place_id: str) -> dict | None:
    """
    Fetch artwork title and id from Art Institute API.
    Uses an in-memory cache to avoid repeated requests for the same artwork.
    If the external API responds with HTTP 429, the request is retried once
    after a short delay before returning an error.
    Args:
        external_place_id: Artwork identifier from the Art Institute API.
    Returns:
        dict with 'id' and 'title', or None if not found.

    Raises:
        HTTPException:
            - 503 Service Unavailable: If the external API is unavailable
              or the rate limit is exceeded after retrying.
    """
    # Return cached result if available
    if external_place_id in _place_existence_cache:
        cached = _place_existence_cache[external_place_id]
        return None if cached is False else cached

    url = f"{settings.ARTIC_API_URL.rstrip('/')}/artworks/{external_place_id}"

    async with httpx.AsyncClient() as client:
        max_attempts = 2

        for attempt in range(max_attempts):
            try:
                response = await client.get(url, params={"fields": "id, title"}, timeout=4.0)

                if response.status_code == status.HTTP_200_OK:
                    data = response.json().get("data") or {}
                    result = {
                        "id": str(data.get("id", external_place_id)),
                        "title": data.get("title", "Unknown Place")
                    }
                    _place_existence_cache[external_place_id] = result
                    return result

                if response.status_code == status.HTTP_404_NOT_FOUND:
                    _place_existence_cache[external_place_id] = False
                    return None

                # Retry once if the API rate limit is exceeded (HTTP 429)
                if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS and attempt == 0:
                    await asyncio.sleep(1.0)
                    continue

                # Raise an error if the retry also fails due to rate limiting
                if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="External API rate limit exceeded after retry. Please try again later."
                    )

                return None

            except httpx.RequestError:
                # Retry once on a temporary network error
                if attempt == 0:
                    await asyncio.sleep(0.5)
                    continue
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="External API is temporarily unavailable."
                )

        return None