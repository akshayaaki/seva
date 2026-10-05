"""
Janseva AI — OSRM Route Optimization Service
Uses OpenStreetMap Routing Machine for real route calculations.
"""
import httpx
import structlog
from typing import Optional
from app.config import get_settings

logger = structlog.get_logger()


class RoutingService:
    """
    Real route optimization using OSRM.
    Returns actual distances, durations, and route geometry.
    """

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.osrm_url

    async def get_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> Optional[dict]:
        """
        Get a real driving route between two points.
        Returns distance, duration, and geometry.
        """
        try:
            coords = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
            url = f"{self.base_url}/route/v1/driving/{coords}"

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    url,
                    params={
                        "overview": "full",
                        "geometries": "geojson",
                        "steps": "false",
                    },
                )
                response.raise_for_status()
                data = response.json()

                if data.get("code") != "Ok" or not data.get("routes"):
                    logger.warning(
                        "osrm_no_route",
                        code=data.get("code"),
                        origin=f"{origin_lat},{origin_lon}",
                        dest=f"{dest_lat},{dest_lon}",
                    )
                    return None

                route = data["routes"][0]
                return {
                    "distance_meters": route["distance"],
                    "duration_seconds": route["duration"],
                    "geometry": route["geometry"],
                }

        except httpx.TimeoutException:
            logger.error("osrm_timeout")
            return None
        except Exception as e:
            logger.error("osrm_error", error=str(e))
            return None

    async def get_trip(
        self,
        waypoints: list[tuple[float, float]],
    ) -> Optional[dict]:
        """
        Optimize a multi-stop trip (traveling salesman).
        waypoints: list of (lat, lon) tuples
        """
        if len(waypoints) < 2:
            return None

        try:
            coords = ";".join(f"{lon},{lat}" for lat, lon in waypoints)
            url = f"{self.base_url}/trip/v1/driving/{coords}"

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    url,
                    params={
                        "overview": "full",
                        "geometries": "geojson",
                        "roundtrip": "false",
                        "source": "first",
                        "destination": "last",
                    },
                )
                response.raise_for_status()
                data = response.json()

                if data.get("code") != "Ok" or not data.get("trips"):
                    logger.warning("osrm_trip_no_route", code=data.get("code"))
                    return None

                trip = data["trips"][0]
                return {
                    "distance_meters": trip["distance"],
                    "duration_seconds": trip["duration"],
                    "geometry": trip["geometry"],
                    "waypoint_order": [
                        wp["waypoint_index"] for wp in data.get("waypoints", [])
                    ],
                }

        except httpx.TimeoutException:
            logger.error("osrm_trip_timeout")
            return None
        except Exception as e:
            logger.error("osrm_trip_error", error=str(e))
            return None


_routing_service: Optional[RoutingService] = None


def get_routing_service() -> RoutingService:
    global _routing_service
    if _routing_service is None:
        _routing_service = RoutingService()
    return _routing_service
