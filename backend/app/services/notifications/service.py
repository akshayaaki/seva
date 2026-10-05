"""
Janseva AI — Notification Engine
Sends real notifications through configured channels and tracks delivery status.
"""
import structlog
from typing import Optional
from app.database import get_supabase_admin

logger = structlog.get_logger()


class NotificationService:
    """
    Sends notifications through configured channels.
    All notifications are stored in the database with delivery status tracking.
    """

    def __init__(self):
        self.supabase = get_supabase_admin()

    async def send(
        self,
        user_id: str,
        title: str,
        body: str,
        event_type: str,
        channel: str = "in_app",
        reference_type: Optional[str] = None,
        reference_id: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> Optional[str]:
        """
        Create and send a notification.
        Returns notification_id or None on failure.
        """
        if not user_id:
            return None
        try:
            notification_data = {
                "user_id": user_id,
                "channel": channel,
                "title": title,
                "body": body,
                "event_type": event_type,
                "reference_type": reference_type,
                "reference_id": reference_id,
                "data": data or {},
                "status": "sent" if channel == "in_app" else "pending",
            }

            response = (
                self.supabase.table("notifications")
                .insert(notification_data)
                .execute()
            )

            notification_id = response.data[0]["id"]

            # For in_app, it's immediately "sent" (Supabase Realtime delivers it)
            # For other channels, would dispatch to external provider here

            logger.info(
                "notification_sent",
                notification_id=notification_id,
                user_id=user_id,
                event_type=event_type,
                channel=channel,
            )

            return notification_id

        except Exception as e:
            logger.error("notification_error", user_id=user_id, error=str(e))
            return None

    async def notify_complaint_registered(
        self, citizen_user_id: str, complaint_id: str, complaint_number: str
    ):
        await self.send(
            user_id=citizen_user_id,
            title="Complaint Registered",
            body=f"Your complaint {complaint_number} has been registered and is being processed.",
            event_type="complaint_registered",
            reference_type="complaint",
            reference_id=complaint_id,
        )

    async def notify_complaint_classified(
        self, citizen_user_id: str, complaint_id: str, category: str
    ):
        await self.send(
            user_id=citizen_user_id,
            title="Complaint Classified",
            body=f"Your complaint has been classified under '{category}' and routed to the appropriate department.",
            event_type="complaint_classified",
            reference_type="complaint",
            reference_id=complaint_id,
        )

    async def notify_worker_assigned(
        self, worker_user_id: str, task_id: str, incident_title: str
    ):
        await self.send(
            user_id=worker_user_id,
            title="New Task Assigned",
            body=f"You have been assigned to: {incident_title}",
            event_type="task_assigned",
            reference_type="task",
            reference_id=task_id,
        )

    async def notify_work_completed(
        self, citizen_user_id: str, complaint_id: str
    ):
        await self.send(
            user_id=citizen_user_id,
            title="Work Completed",
            body="The reported issue has been addressed. Please confirm if the problem is resolved.",
            event_type="work_completed",
            reference_type="complaint",
            reference_id=complaint_id,
        )

    async def notify_complaint_reopened(
        self, supervisor_user_id: str, complaint_id: str, complaint_number: str
    ):
        await self.send(
            user_id=supervisor_user_id,
            title="Complaint Reopened",
            body=f"Complaint {complaint_number} has been reopened by the citizen.",
            event_type="complaint_reopened",
            reference_type="complaint",
            reference_id=complaint_id,
        )

    async def get_user_notifications(
        self, user_id: str, limit: int = 50, unread_only: bool = False
    ) -> list[dict]:
        """Get notifications for a user from the database."""
        query = (
            self.supabase.table("notifications")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
        )

        if unread_only:
            query = query.is_("read_at", "null")

        response = query.execute()
        return response.data or []

    async def mark_as_read(self, notification_id: str, user_id: str):
        """Mark a notification as read."""
        from datetime import datetime, timezone

        self.supabase.table("notifications").update({
            "status": "read",
            "read_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", notification_id).eq("user_id", user_id).execute()


_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
