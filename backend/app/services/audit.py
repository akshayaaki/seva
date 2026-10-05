"""
Janseva AI — Audit Logging Service
Records all important system events with actor, action, entity, and values.
"""
import structlog
from typing import Optional
from app.database import get_supabase_admin

logger = structlog.get_logger()


class AuditService:
    """Tamper-resistant audit logging backed by the database."""

    def __init__(self):
        self.supabase = get_supabase_admin()

    async def log(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_role: Optional[str] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
        reason: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """Record an audit event."""
        import uuid as _uuid
        try:
            clean_actor_id = None
            if actor_id:
                try:
                    _uuid.UUID(str(actor_id))
                    clean_actor_id = str(actor_id)
                except ValueError:
                    clean_actor_id = None

            clean_entity_id = None
            if entity_id:
                try:
                    _uuid.UUID(str(entity_id))
                    clean_entity_id = str(entity_id)
                except ValueError:
                    clean_entity_id = None

            clean_role = actor_role if actor_role in ('citizen', 'worker', 'supervisor', 'department_officer', 'municipal_admin', 'system_admin') else None

            self.supabase.table("audit_logs").insert({
                "actor_id": clean_actor_id,
                "actor_role": clean_role,
                "action": action,
                "entity_type": entity_type,
                "entity_id": clean_entity_id,
                "old_value": old_value,
                "new_value": new_value,
                "reason": reason,
                "ip_address": ip_address,
                "user_agent": user_agent,
            }).execute()

            logger.info(
                "audit_logged",
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                actor_id=actor_id,
            )
        except Exception as e:
            # Audit log failure should not crash the main operation
            logger.error("audit_log_error", action=action, error=str(e))

    async def get_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict]:
        """Query audit logs with filters."""
        query = (
            self.supabase.table("audit_logs")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
        )

        if entity_type:
            query = query.eq("entity_type", entity_type)
        if entity_id:
            query = query.eq("entity_id", entity_id)
        if action:
            query = query.eq("action", action)

        response = query.execute()
        return response.data or []


_audit_service: Optional[AuditService] = None


def get_audit_service() -> AuditService:
    global _audit_service
    if _audit_service is None:
        _audit_service = AuditService()
    return _audit_service
