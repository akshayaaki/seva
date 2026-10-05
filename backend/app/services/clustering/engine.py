"""
Janseva AI — Incident Clustering Engine
Groups similar complaints into master incidents based on real signals.
"""
import structlog
from typing import Optional
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta, timezone
from app.database import get_supabase_admin

logger = structlog.get_logger()

# Clustering thresholds (configurable)
DISTANCE_THRESHOLD_KM = 0.5  # Max distance between complaints in same cluster
TIME_THRESHOLD_HOURS = 72  # Max time difference
CATEGORY_WEIGHT = 0.4
PROXIMITY_WEIGHT = 0.35
TIME_WEIGHT = 0.15
TEXT_WEIGHT = 0.10
MERGE_THRESHOLD = 0.60  # Minimum similarity to merge


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


class IncidentClusteringEngine:
    """
    Clusters complaints into master incidents using geographic proximity,
    time, category, and text similarity signals.

    Does NOT merge solely on category — requires multi-signal confirmation.
    """

    def __init__(self):
        self.supabase = get_supabase_admin()

    async def find_matching_incident(
        self,
        complaint_id: str,
        category: Optional[str],
        latitude: Optional[float],
        longitude: Optional[float],
        summary: Optional[str],
        municipality_id: Optional[str],
    ) -> Optional[str]:
        """
        Check if this complaint matches an existing open incident.
        Returns incident_id if a match is found, None otherwise.
        """
        if not municipality_id:
            return None

        # Get recent open incidents in the same municipality
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=TIME_THRESHOLD_HOURS)).isoformat()

        incidents_response = (
            self.supabase.table("master_incidents")
            .select("*, locations(*)")
            .eq("municipality_id", municipality_id)
            .in_("status", ["open", "triaged", "assigned", "in_progress"])
            .gte("created_at", cutoff)
            .execute()
        )

        incidents = incidents_response.data or []
        if not incidents:
            return None

        best_match_id = None
        best_score = 0.0

        for incident in incidents:
            score = 0.0

            # Category match
            if category and incident.get("category"):
                if category.lower() == incident["category"].lower():
                    score += CATEGORY_WEIGHT
                elif self._categories_related(category, incident["category"]):
                    score += CATEGORY_WEIGHT * 0.5

            # Geographic proximity
            if latitude and longitude and incident.get("locations"):
                loc = incident["locations"]
                inc_lat = loc.get("latitude")
                inc_lon = loc.get("longitude")
                if inc_lat and inc_lon:
                    dist = haversine_km(latitude, longitude, inc_lat, inc_lon)
                    if dist <= DISTANCE_THRESHOLD_KM:
                        proximity_score = max(0, 1.0 - dist / DISTANCE_THRESHOLD_KM)
                        score += PROXIMITY_WEIGHT * proximity_score

            # Time proximity
            if incident.get("created_at"):
                try:
                    inc_time = datetime.fromisoformat(
                        incident["created_at"].replace("Z", "+00:00")
                    )
                    hours_diff = abs(
                        (datetime.now(timezone.utc) - inc_time).total_seconds() / 3600
                    )
                    if hours_diff <= TIME_THRESHOLD_HOURS:
                        time_score = max(0, 1.0 - hours_diff / TIME_THRESHOLD_HOURS)
                        score += TIME_WEIGHT * time_score
                except (ValueError, TypeError):
                    pass

            # Basic text similarity (keyword overlap)
            if summary and incident.get("description"):
                text_sim = self._text_similarity(summary, incident["description"])
                score += TEXT_WEIGHT * text_sim

            if score > best_score and score >= MERGE_THRESHOLD:
                best_score = score
                best_match_id = incident["id"]

        if best_match_id:
            logger.info(
                "incident_match_found",
                complaint_id=complaint_id,
                incident_id=best_match_id,
                score=round(best_score, 3),
            )

        return best_match_id

    async def create_incident(
        self,
        complaint_id: str,
        title: str,
        description: str,
        category: Optional[str],
        subcategory: Optional[str],
        department_id: Optional[str],
        location_id: Optional[str],
        latitude: Optional[float],
        longitude: Optional[float],
        severity: Optional[str],
        safety_risk: bool,
        estimated_affected: Optional[int],
        municipality_id: Optional[str],
        ward_id: Optional[str],
        priority_score: Optional[float],
        priority_level: Optional[str],
        priority_reasons: Optional[list],
    ) -> str:
        """Create a new master incident and link the complaint."""
        incident_data = {
            "title": title,
            "description": description,
            "status": "open",
            "category": category,
            "subcategory": subcategory,
            "department_id": department_id,
            "location_id": location_id,
            "severity": severity,
            "safety_risk": safety_risk,
            "estimated_affected_population": estimated_affected,
            "municipality_id": municipality_id,
            "ward_id": ward_id,
            "complaint_count": 1,
            "priority_score": priority_score,
            "priority_level": priority_level,
            "priority_reasons": priority_reasons,
        }

        response = (
            self.supabase.table("master_incidents")
            .insert(incident_data)
            .execute()
        )
        incident_id = response.data[0]["id"]

        # Link complaint to incident
        self.supabase.table("incident_complaints").insert({
            "incident_id": incident_id,
            "complaint_id": complaint_id,
            "similarity_score": 1.0,
            "linked_by": "system_creation",
        }).execute()

        # Update complaint
        self.supabase.table("complaints").update({
            "master_incident_id": incident_id,
        }).eq("id", complaint_id).execute()

        logger.info("incident_created", incident_id=incident_id, complaint_id=complaint_id)
        return incident_id

    async def add_to_incident(
        self, complaint_id: str, incident_id: str, similarity_score: float
    ):
        """Add a complaint to an existing incident."""
        # Link
        self.supabase.table("incident_complaints").insert({
            "incident_id": incident_id,
            "complaint_id": complaint_id,
            "similarity_score": similarity_score,
            "linked_by": "auto_clustering",
        }).execute()

        # Update complaint
        self.supabase.table("complaints").update({
            "master_incident_id": incident_id,
        }).eq("id", complaint_id).execute()

        # Update incident complaint count
        incident = (
            self.supabase.table("master_incidents")
            .select("complaint_count")
            .eq("id", incident_id)
            .single()
            .execute()
        )
        new_count = (incident.data.get("complaint_count", 0) or 0) + 1
        self.supabase.table("master_incidents").update({
            "complaint_count": new_count,
        }).eq("id", incident_id).execute()

        logger.info(
            "complaint_added_to_incident",
            complaint_id=complaint_id,
            incident_id=incident_id,
            new_count=new_count,
        )

    def _categories_related(self, cat1: str, cat2: str) -> bool:
        """Check if two categories are semantically related."""
        related_groups = [
            {"drainage", "sewage", "water_supply"},
            {"roads", "traffic"},
            {"street_lights", "electricity"},
            {"garbage", "public_health"},
            {"parks", "encroachment"},
        ]
        for group in related_groups:
            if cat1.lower() in group and cat2.lower() in group:
                return True
        return False

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple keyword overlap similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        # Remove common words
        stopwords = {"the", "a", "an", "is", "in", "at", "to", "of", "and", "or", "has", "been", "our", "my", "this", "that"}
        words1 -= stopwords
        words2 -= stopwords
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union) if union else 0.0


_clustering_engine: Optional[IncidentClusteringEngine] = None


def get_clustering_engine() -> IncidentClusteringEngine:
    global _clustering_engine
    if _clustering_engine is None:
        _clustering_engine = IncidentClusteringEngine()
    return _clustering_engine
