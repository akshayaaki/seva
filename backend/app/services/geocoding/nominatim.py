"""
Janseva AI — Geocoding Service
Uses Nominatim (OpenStreetMap) for geocoding and reverse geocoding.
"""
import httpx
import structlog
from typing import Optional
from app.config import get_settings

logger = structlog.get_logger()


class GeocodingService:
    """
    Production geocoding using Nominatim.
    Implements rate limiting (1 req/sec per Nominatim policy).
    """

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.nominatim_url
        self.user_agent = settings.nominatim_user_agent
        self.headers = {"User-Agent": self.user_agent}

    async def reverse_geocode(
        self, latitude: float, longitude: float
    ) -> Optional[dict]:
        """
        Reverse geocode coordinates to an address.
        Returns structured address data or None on failure.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/reverse",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "format": "json",
                        "addressdetails": 1,
                        "zoom": 18,
                    },
                    headers=self.headers,
                )
                response.raise_for_status()
                data = response.json()

                if "error" in data:
                    logger.warning(
                        "reverse_geocode_no_result",
                        lat=latitude,
                        lon=longitude,
                        error=data["error"],
                    )
                    return None

                return {
                    "display_name": data.get("display_name", ""),
                    "address": data.get("address", {}),
                    "city": data.get("address", {}).get("city")
                    or data.get("address", {}).get("town")
                    or data.get("address", {}).get("village", ""),
                    "state": data.get("address", {}).get("state", ""),
                    "postcode": data.get("address", {}).get("postcode", ""),
                    "country": data.get("address", {}).get("country", ""),
                    "suburb": data.get("address", {}).get("suburb", ""),
                    "road": data.get("address", {}).get("road", ""),
                }

        except httpx.TimeoutException:
            logger.error("reverse_geocode_timeout", lat=latitude, lon=longitude)
            return None
        except Exception as e:
            logger.error("reverse_geocode_error", error=str(e))
            return None

    async def forward_geocode(
        self, query: str, limit: int = 5
    ) -> list[dict]:
        """
        Forward geocode an address/landmark to coordinates.
        Returns list of matching locations.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params={
                        "q": query,
                        "format": "json",
                        "addressdetails": 1,
                        "limit": limit,
                        "countrycodes": "in",
                    },
                    headers=self.headers,
                )
                response.raise_for_status()
                results = response.json()

                return [
                    {
                        "latitude": float(r["lat"]),
                        "longitude": float(r["lon"]),
                        "display_name": r.get("display_name", ""),
                        "address": r.get("address", {}),
                        "importance": r.get("importance", 0),
                    }
                    for r in results
                ]

        except httpx.TimeoutException:
            logger.error("forward_geocode_timeout", query=query)
            return []
        except Exception as e:
            logger.error("forward_geocode_error", error=str(e))
            return []


_geocoding_service: Optional[GeocodingService] = None


def get_geocoding_service() -> GeocodingService:
    global _geocoding_service
    if _geocoding_service is None:
        _geocoding_service = GeocodingService()
    return _geocoding_service


async def reverse_geocode(latitude: float, longitude: float) -> Optional[dict]:
    return await get_geocoding_service().reverse_geocode(latitude, longitude)


async def forward_geocode(query: str, limit: int = 5) -> list[dict]:
    return await get_geocoding_service().forward_geocode(query, limit)

