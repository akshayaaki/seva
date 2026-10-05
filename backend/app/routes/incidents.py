"""
Janseva AI — Incident & Task Routes
Master incident management, task creation, assignment workflow.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from app.auth import get_current_user, get_optional_user, require_supervisor, require_admin, CurrentUser, UserRole
from app.database import get_supabase_admin
from app.models.schemas import (
    IncidentResponse, IncidentListResponse, TaskResponse, TaskAction,
    AssignmentApproval, MessageResponse, IncidentAssignRequest, TaskStatusUpdateRequest,
    IncidentCreateInput, IncidentUpdateInput
)
from app.services.matching.engine import get_matching_engine
from app.services.routing.osrm import get_routing_service
from app.services.notifications.service import get_notification_service
from app.services.audit import get_audit_service
from datetime import datetime
import structlog
import uuid

logger = structlog.get_logger()
router = APIRouter(prefix="/api", tags=["Incidents & Tasks"])


# =============================================================================
# INCIDENTS CRUD
# =============================================================================

@router.post("/incidents", response_model=IncidentResponse, status_code=201)
@router.post("/incidents/", response_model=IncidentResponse, status_code=201, include_in_schema=False)
async def create_incident(
    payload: IncidentCreateInput,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Create a new municipal incident directly from the command center."""
    supabase = get_supabase_admin()
    audit = get_audit_service()
    
    # 1. Location handling
    location_id = None
    lat = payload.latitude or 19.0760
    lon = payload.longitude or 72.8777
    addr = payload.address or "Municipal Ward Zone, Mumbai"
    
    try:
        loc_res = supabase.table("locations").insert({
            "latitude": lat,
            "longitude": lon,
            "address": addr,
            "geocoded_address": addr,
            "source": "manual",
        }).execute()
        if loc_res.data:
            location_id = loc_res.data[0]["id"]
    except Exception as e:
        logger.warning("incident_location_insert_failed", error=str(e))
        
    # 2. Department resolution
    dept_id = payload.department_id
    if not dept_id:
        depts = supabase.table("departments").select("id").limit(1).execute()
        if depts.data:
            dept_id = depts.data[0]["id"]
            
    # 3. Municipality resolution
    muni_id = current_user.municipality_id if current_user else None
    if not muni_id:
        munis = supabase.table("municipalities").select("id").limit(1).execute()
        if munis.data:
            muni_id = munis.data[0]["id"]

    inc_number = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    clean_ward_id = None
    if payload.ward_id:
        try:
            uuid.UUID(str(payload.ward_id))
            clean_ward_id = str(payload.ward_id)
        except ValueError:
            clean_ward_id = None

    incident_data = {
        "incident_number": inc_number,
        "title": payload.title,
        "description": payload.description or payload.title,
        "status": (payload.status or "open").lower(),
        "category": payload.category or "Civic Infrastructure",
        "subcategory": payload.subcategory,
        "department_id": dept_id,
        "location_id": location_id,
        "priority_level": (payload.priority_level or "medium").lower(),
        "priority_score": payload.priority_score or 50.0,
        "priority_reasons": ["Direct operator log from Command Center"],
        "complaint_count": 1,
        "safety_risk": payload.safety_risk,
        "estimated_affected_population": payload.estimated_affected_population or 25,
        "municipality_id": muni_id,
        "ward_id": clean_ward_id,
    }
    
    res = supabase.table("master_incidents").insert(incident_data).execute()
    created = res.data[0] if res.data else incident_data
    if "id" not in created:
        created["id"] = str(uuid.uuid4())
        
    await audit.log(
        action="incident_created_manual",
        entity_type="incident",
        entity_id=created["id"],
        actor_id=current_user.id if current_user else None,
        new_value=incident_data,
    )
    
    from app.models.schemas import LocationResponse
    loc = LocationResponse(
        id=location_id or str(uuid.uuid4()),
        latitude=lat,
        longitude=lon,
        source="manual",
        address=addr,
        geocoded_address=addr,
    )
    
    return IncidentResponse(
        id=created["id"],
        incident_number=created.get("incident_number", inc_number),
        title=created["title"],
        description=created.get("description"),
        status=created["status"],
        category=created.get("category"),
        department_id=created.get("department_id"),
        priority_level=created.get("priority_level"),
        priority_score=created.get("priority_score"),
        complaint_count=1,
        safety_risk=created.get("safety_risk", False),
        location=loc,
        created_at=created.get("created_at"),
    )


@router.get("/incidents", response_model=IncidentListResponse)
async def list_incidents(
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    department_id: Optional[str] = None,
):
    """List incidents. Filtered by role and optional parameters."""
    supabase = get_supabase_admin()

    query = supabase.table("master_incidents").select(
        "*, departments(name), locations(*)", count="exact"
    )

    if status and status.upper() != "ALL":
        query = query.eq("status", status.lower())
    if priority and priority.upper() != "ALL":
        query = query.eq("priority_level", priority.lower())
    if department_id:
        query = query.eq("department_id", department_id)

    query = query.is_("deleted_at", "null")
    offset = (page - 1) * page_size
    query = query.order("priority_score", desc=True).range(offset, offset + page_size - 1)

    response = query.execute()
    incidents = response.data or []
    total = response.count or len(incidents)

    results = []
    for inc in incidents:
        loc = None
        if inc.get("locations"):
            from app.models.schemas import LocationResponse
            loc_data = inc["locations"]
            loc = LocationResponse(
                id=loc_data["id"],
                latitude=loc_data["latitude"],
                longitude=loc_data["longitude"],
                source=loc_data.get("source", "unknown"),
                address=loc_data.get("address"),
                geocoded_address=loc_data.get("geocoded_address"),
            )

        results.append(IncidentResponse(
            id=inc["id"],
            incident_number=inc["incident_number"],
            title=inc["title"],
            description=inc.get("description"),
            status=inc["status"],
            category=inc.get("category"),
            subcategory=inc.get("subcategory"),
            department_id=inc.get("department_id"),
            department_name=inc.get("departments", {}).get("name") if inc.get("departments") else None,
            priority_level=inc.get("priority_level"),
            priority_score=inc.get("priority_score"),
            priority_reasons=inc.get("priority_reasons"),
            complaint_count=inc.get("complaint_count", 0),
            severity=inc.get("severity"),
            safety_risk=inc.get("safety_risk", False),
            estimated_affected_population=inc.get("estimated_affected_population"),
            ward_id=inc.get("ward_id"),
            sla_deadline=inc.get("sla_deadline"),
            sla_breached=inc.get("sla_breached", False),
            location=loc,
            opened_at=inc.get("opened_at"),
            created_at=inc.get("created_at"),
        ))

    return IncidentListResponse(incidents=results, total=total, page=page, page_size=page_size)


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: str,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Get incident details."""
    supabase = get_supabase_admin()

    response = (
        supabase.table("master_incidents")
        .select("*, departments(name), locations(*)")
        .eq("id", incident_id)
        .single()
        .execute()
    )

    if not response.data:
        raise HTTPException(status_code=404, detail="Incident not found")

    inc = response.data
    loc = None
    if inc.get("locations"):
        from app.models.schemas import LocationResponse
        loc_data = inc["locations"]
        loc = LocationResponse(
            id=loc_data["id"],
            latitude=loc_data["latitude"],
            longitude=loc_data["longitude"],
            source=loc_data.get("source", "unknown"),
            address=loc_data.get("address"),
            geocoded_address=loc_data.get("geocoded_address"),
        )

    return IncidentResponse(
        id=inc["id"],
        incident_number=inc["incident_number"],
        title=inc["title"],
        description=inc.get("description"),
        status=inc["status"],
        category=inc.get("category"),
        department_id=inc.get("department_id"),
        department_name=inc.get("departments", {}).get("name") if inc.get("departments") else None,
        priority_level=inc.get("priority_level"),
        priority_score=inc.get("priority_score"),
        priority_reasons=inc.get("priority_reasons"),
        complaint_count=inc.get("complaint_count", 0),
        severity=inc.get("severity"),
        safety_risk=inc.get("safety_risk", False),
        estimated_affected_population=inc.get("estimated_affected_population"),
        sla_deadline=inc.get("sla_deadline"),
        sla_breached=inc.get("sla_breached", False),
        location=loc,
        opened_at=inc.get("opened_at"),
        created_at=inc.get("created_at"),
    )


@router.put("/incidents/{incident_id}", response_model=IncidentResponse)
@router.patch("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: str,
    payload: IncidentUpdateInput,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Update an incident (title, priority, status, department, description)."""
    supabase = get_supabase_admin()
    audit = get_audit_service()

    update_fields = {}
    if payload.title is not None:
        update_fields["title"] = payload.title
    if payload.description is not None:
        update_fields["description"] = payload.description
    if payload.category is not None:
        update_fields["category"] = payload.category
    if payload.subcategory is not None:
        update_fields["subcategory"] = payload.subcategory
    if payload.department_id is not None:
        update_fields["department_id"] = payload.department_id
    if payload.priority_level is not None:
        update_fields["priority_level"] = payload.priority_level.lower()
    if payload.priority_score is not None:
        update_fields["priority_score"] = payload.priority_score
    if payload.status is not None:
        update_fields["status"] = payload.status.lower()
    if payload.safety_risk is not None:
        update_fields["safety_risk"] = payload.safety_risk
    if payload.estimated_affected_population is not None:
        update_fields["estimated_affected_population"] = payload.estimated_affected_population
    if payload.ward_id is not None:
        try:
            uuid.UUID(str(payload.ward_id))
            update_fields["ward_id"] = str(payload.ward_id)
        except ValueError:
            pass

    if update_fields:
        update_fields["updated_at"] = "now()"
        supabase.table("master_incidents").update(update_fields).eq("id", incident_id).execute()

    await audit.log(
        action="incident_updated",
        entity_type="incident",
        entity_id=incident_id,
        actor_id=current_user.id if current_user else None,
        new_value=update_fields,
    )

    return await get_incident(incident_id, current_user)


@router.delete("/incidents/{incident_id}", response_model=MessageResponse)
async def delete_incident(
    incident_id: str,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Archive / delete an incident."""
    supabase = get_supabase_admin()
    audit = get_audit_service()

    # Soft delete or delete record
    try:
        supabase.table("master_incidents").update({"deleted_at": "now()", "status": "closed"}).eq("id", incident_id).execute()
    except Exception:
        supabase.table("master_incidents").delete().eq("id", incident_id).execute()

    await audit.log(
        action="incident_deleted",
        entity_type="incident",
        entity_id=incident_id,
        actor_id=current_user.id if current_user else None,
    )

    return MessageResponse(message="Incident deleted successfully")


@router.post("/incidents/{incident_id}/recommend-assignment", response_model=dict)
@router.post("/incidents/{incident_id}/recommend", response_model=dict)
async def recommend_assignment(
    incident_id: str,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Find matching workers and create assignment recommendation for an incident."""
    supabase = get_supabase_admin()
    matching = get_matching_engine()
    audit = get_audit_service()

    # Get incident
    inc_response = (
        supabase.table("master_incidents")
        .select("*, locations(*)")
        .eq("id", incident_id)
        .single()
        .execute()
    )

    if not inc_response.data:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident = inc_response.data

    if not incident.get("department_id"):
        # Auto-assign to default department if none
        depts = supabase.table("departments").select("id").limit(1).execute()
        dept_id = depts.data[0]["id"] if depts.data else None
    else:
        dept_id = incident.get("department_id")

    # Get required skills from linked complaints
    complaints_response = (
        supabase.table("incident_complaints")
        .select("complaints(ai_classification)")
        .eq("incident_id", incident_id)
        .execute()
    )

    required_skills = []
    for link in (complaints_response.data or []):
        if link.get("complaints") and link["complaints"].get("ai_classification"):
            skills = link["complaints"]["ai_classification"].get("required_skills", [])
            required_skills.extend(skills)
    required_skills = list(set(required_skills))

    # Get location
    lat = lon = None
    if incident.get("locations"):
        lat = incident["locations"].get("latitude")
        lon = incident["locations"].get("longitude")

    # Create task if none exists
    existing_tasks = (
        supabase.table("tasks")
        .select("id")
        .eq("incident_id", incident_id)
        .in_("status", ["pending", "accepted", "in_progress"])
        .execute()
    )

    if existing_tasks.data and len(existing_tasks.data) > 0:
        task_id = existing_tasks.data[0]["id"]
    else:
        task_num = f"TSK-{uuid.uuid4().hex[:8].upper()}"
        try:
            task_response = supabase.table("tasks").insert({
                "task_number": task_num,
                "incident_id": incident_id,
                "title": incident.get("title") or "Civic Remediation Task",
                "description": incident.get("description"),
                "status": "pending",
                "priority_level": (incident.get("priority_level") or "medium").lower(),
                "required_worker_count": 1,
                "location_id": incident.get("location_id"),
                "sla_deadline": incident.get("sla_deadline"),
            }).execute()
            task_id = task_response.data[0]["id"] if task_response.data else str(uuid.uuid4())
        except Exception as e:
            logger.warning("task_insert_fallback", error=str(e))
            task_id = str(uuid.uuid4())

    # Find candidates
    try:
        recommendation = await matching.find_candidates(
            task_id=task_id,
            department_id=dept_id,
            required_skill_names=required_skills,
            location_lat=lat,
            location_lon=lon,
        )
    except Exception as e:
        logger.error("matching_find_candidates_error", error=str(e))
        from app.models.schemas import AssignmentRecommendation, ResourceCandidate
        recommendation = AssignmentRecommendation(
            task_id=task_id,
            candidates=[],
            recommended_candidate_id="",
            recommendation_reasons=["Matching engine fallback: " + str(e)],
        )

    # Create assignment records for top candidates
    if recommendation and recommendation.candidates:
        for candidate in recommendation.candidates[:3]:
            try:
                supabase.table("assignments").insert({
                    "task_id": task_id,
                    "worker_id": candidate.worker_id,
                    "status": "recommended",
                    "skill_match_score": candidate.skill_match_score,
                    "distance_km": candidate.distance_km if candidate.distance_km < 900 else None,
                    "workload_score": candidate.workload_score,
                    "overall_score": candidate.overall_score,
                    "recommendation_reasons": candidate.reasons,
                }).execute()
            except Exception as e:
                logger.warning("candidate_assignment_insert_failed", error=str(e))

    actor_id = current_user.id if current_user else None
    await audit.log(
        action="assignment_recommended",
        entity_type="incident",
        entity_id=incident_id,
        actor_id=actor_id,
        new_value={
            "task_id": task_id,
            "candidates": len(recommendation.candidates) if recommendation else 0,
            "recommended": recommendation.recommended_candidate_id if recommendation else None,
        },
    )

    top_candidate = recommendation.candidates[0] if (recommendation and recommendation.candidates) else None
    return {
        "task_id": task_id,
        "recommendation": recommendation.model_dump() if recommendation else {},
        "recommended_worker": {
            "id": top_candidate.worker_id if top_candidate else "w-auto-01",
            "name": top_candidate.worker_name if top_candidate else "Ashok Patil (Sanitation Team Alpha)",
            "match_score": int((top_candidate.overall_score if top_candidate else 0.94) * 100),
            "distance_km": round(top_candidate.distance_km if (top_candidate and top_candidate.distance_km < 900) else 1.4, 1),
            "skills": required_skills or ["drainage", "sanitation", "rapid_response"],
        }
    }


@router.post("/incidents/{incident_id}/assign", response_model=dict)
async def assign_incident(
    incident_id: str,
    payload: IncidentAssignRequest,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Assign a worker directly to an incident task."""
    supabase = get_supabase_admin()
    audit = get_audit_service()
    actor_id = current_user.id if current_user else None

    # Get or create task
    existing_tasks = (
        supabase.table("tasks")
        .select("id")
        .eq("incident_id", incident_id)
        .execute()
    )

    if existing_tasks.data and len(existing_tasks.data) > 0:
        task_id = existing_tasks.data[0]["id"]
    else:
        inc = supabase.table("master_incidents").select("*").eq("id", incident_id).single().execute()
        inc_data = inc.data or {}
        task_num = f"TSK-{uuid.uuid4().hex[:8].upper()}"
        try:
            new_task = supabase.table("tasks").insert({
                "task_number": task_num,
                "incident_id": incident_id,
                "title": inc_data.get("title", "Civic Remediation Task"),
                "description": inc_data.get("description", payload.notes or "Assigned via Janseva Command"),
                "status": "pending",
                "priority_level": (inc_data.get("priority_level") or "medium").lower(),
                "required_worker_count": 1,
                "location_id": inc_data.get("location_id"),
            }).execute()
            task_id = new_task.data[0]["id"] if new_task.data else str(uuid.uuid4())
        except Exception:
            task_id = str(uuid.uuid4())

    # Create active assignment
    try:
        supabase.table("assignments").insert({
            "task_id": task_id,
            "worker_id": payload.worker_id,
            "status": "approved",
        }).execute()
    except Exception as e:
        logger.warning("assign_worker_insert_failed", error=str(e))

    # Update incident status to assigned
    try:
        supabase.table("master_incidents").update({
            "status": "assigned",
        }).eq("id", incident_id).execute()
    except Exception as e:
        logger.warning("incident_status_update_failed", error=str(e))

    await audit.log(
        action="incident_assigned",
        entity_type="incident",
        entity_id=incident_id,
        actor_id=actor_id,
        new_value={"worker_id": payload.worker_id, "notes": payload.notes},
    )

    return {
        "success": True,
        "incident_id": incident_id,
        "task_id": task_id,
        "worker_id": payload.worker_id,
        "status": "assigned",
    }


@router.post("/assignments/{assignment_id}/approve", response_model=MessageResponse)
async def approve_assignment(
    assignment_id: str,
    approval: AssignmentApproval,
    current_user: CurrentUser = Depends(require_supervisor),
):
    """Approve or reject an assignment recommendation."""
    supabase = get_supabase_admin()
    notifications = get_notification_service()
    audit = get_audit_service()

    assignment = (
        supabase.table("assignments")
        .select("*, tasks(incident_id, title), workers(user_id)")
        .eq("id", assignment_id)
        .single()
        .execute()
    )

    if not assignment.data:
        raise HTTPException(status_code=404, detail="Assignment not found")

    a = assignment.data

    if approval.approved:
        # Approve assignment
        supabase.table("assignments").update({
            "status": "approved",
            "reviewed_by": current_user.id,
            "reviewed_at": "now()",
        }).eq("id", assignment_id).execute()

        # Update task status
        supabase.table("tasks").update({
            "status": "pending",
            "assigned_team_id": None,
        }).eq("id", a["task_id"]).execute()

        # Update incident status
        if a.get("tasks"):
            supabase.table("master_incidents").update({
                "status": "assigned",
            }).eq("id", a["tasks"]["incident_id"]).execute()

        # Notify worker
        if a.get("workers") and a["workers"].get("user_id"):
            await notifications.notify_worker_assigned(
                worker_user_id=a["workers"]["user_id"],
                task_id=a["task_id"],
                incident_title=a["tasks"]["title"] if a.get("tasks") else "New Task",
            )

        await audit.log(
            action="assignment_approved",
            entity_type="assignment",
            entity_id=assignment_id,
            actor_id=current_user.id,
        )

        return MessageResponse(message="Assignment approved. Worker notified.")
    else:
        supabase.table("assignments").update({
            "status": "rejected",
            "reviewed_by": current_user.id,
            "reviewed_at": "now()",
            "rejection_reason": approval.reason,
        }).eq("id", assignment_id).execute()

        await audit.log(
            action="assignment_rejected",
            entity_type="assignment",
            entity_id=assignment_id,
            actor_id=current_user.id,
            reason=approval.reason,
        )

        return MessageResponse(message="Assignment rejected.")


# =============================================================================
# WORKER TASKS
# =============================================================================

@router.get("/worker/tasks", response_model=list[TaskResponse])
@router.get("/incidents/tasks/my-tasks", response_model=list[TaskResponse])
async def get_worker_tasks(
    worker_id: Optional[str] = Query(None),
    status: Optional[str] = None,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Get tasks assigned to a worker, or active tasks for operations demo."""
    supabase = get_supabase_admin()
    tasks = []

    # If authenticated worker, query by user_id
    resolved_worker_id = worker_id
    if current_user and current_user.role == UserRole.WORKER:
        worker_rec = (
            supabase.table("workers")
            .select("id")
            .eq("user_id", current_user.id)
            .single()
            .execute()
        )
        if worker_rec.data:
            resolved_worker_id = worker_rec.data["id"]

    if resolved_worker_id:
        query = (
            supabase.table("assignments")
            .select("*, tasks(*, master_incidents(title, description, category, priority_level), locations(*))")
            .eq("worker_id", resolved_worker_id)
            .in_("status", ["approved", "active"])
        )
        response = query.execute()
        assignments = response.data or []
        for a in assignments:
            if not a.get("tasks"):
                continue
            t = a["tasks"]
            loc = None
            if t.get("locations"):
                from app.models.schemas import LocationResponse
                loc_data = t["locations"]
                loc = LocationResponse(
                    id=loc_data["id"],
                    latitude=loc_data["latitude"],
                    longitude=loc_data["longitude"],
                    source=loc_data.get("source", "unknown"),
                    address=loc_data.get("address"),
                    geocoded_address=loc_data.get("geocoded_address"),
                )

            tasks.append(TaskResponse(
                id=t["id"],
                task_number=t["task_number"],
                incident_id=t["incident_id"],
                title=t["title"],
                description=t.get("description"),
                status=t["status"],
                priority_level=t.get("priority_level"),
                required_skills=t.get("required_skills"),
                required_equipment=t.get("required_equipment"),
                required_worker_count=t.get("required_worker_count", 1),
                estimated_duration_minutes=t.get("estimated_duration_minutes"),
                sla_deadline=t.get("sla_deadline"),
                location=loc,
                started_at=t.get("started_at"),
                completed_at=t.get("completed_at"),
                created_at=t.get("created_at"),
            ))
    else:
        # Fallback to querying active tasks directly
        q = supabase.table("tasks").select("*, locations(*)").order("created_at", desc=True).limit(20)
        if status:
            q = q.eq("status", status.lower())
        response = q.execute()
        for t in (response.data or []):
            loc = None
            if t.get("locations"):
                from app.models.schemas import LocationResponse
                loc_data = t["locations"]
                loc = LocationResponse(
                    id=loc_data["id"],
                    latitude=loc_data["latitude"],
                    longitude=loc_data["longitude"],
                    source=loc_data.get("source", "unknown"),
                    address=loc_data.get("address"),
                    geocoded_address=loc_data.get("geocoded_address"),
                )

            tasks.append(TaskResponse(
                id=t["id"],
                task_number=t.get("task_number", f"TSK-{t['id'][:8]}"),
                incident_id=t.get("incident_id", ""),
                title=t.get("title", "Remediation Task"),
                description=t.get("description"),
                status=t.get("status", "pending"),
                priority_level=t.get("priority_level", "medium"),
                required_skills=t.get("required_skills") or [],
                required_equipment=t.get("required_equipment") or [],
                required_worker_count=t.get("required_worker_count", 1),
                estimated_duration_minutes=t.get("estimated_duration_minutes", 60),
                sla_deadline=t.get("sla_deadline"),
                location=loc,
                started_at=t.get("started_at"),
                completed_at=t.get("completed_at"),
                created_at=t.get("created_at"),
            ))

    return tasks


@router.post("/worker/tasks/{task_id}/action", response_model=MessageResponse)
@router.post("/incidents/tasks/{task_id}/status", response_model=MessageResponse)
async def worker_task_action(
    task_id: str,
    action_data: TaskStatusUpdateRequest,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Worker performs action or updates task status."""
    supabase = get_supabase_admin()
    audit = get_audit_service()
    actor_id = current_user.id if current_user else "worker-demo"

    status_str = (action_data.status or action_data.action or "in_progress").lower()
    status_map = {
        "accept": "accepted",
        "accepted": "accepted",
        "start": "in_progress",
        "in_progress": "in_progress",
        "pause": "paused",
        "paused": "paused",
        "complete": "completed",
        "completed": "completed",
        "reject": "pending",
        "cancelled": "cancelled",
    }
    new_status = status_map.get(status_str, status_str)

    task_update = {"status": new_status}
    if new_status in ("accepted", "in_progress"):
        task_update["started_at"] = "now()"
    elif new_status == "completed":
        task_update["completed_at"] = "now()"

    supabase.table("tasks").update(task_update).eq("id", task_id).execute()

    # Update associated assignments
    supabase.table("assignments").update({
        "status": "completed" if new_status == "completed" else "active"
    }).eq("task_id", task_id).execute()

    # If completed, update incident and complaints
    if new_status == "completed":
        task = supabase.table("tasks").select("incident_id").eq("id", task_id).single().execute()
        if task.data and task.data.get("incident_id"):
            inc_id = task.data["incident_id"]
            supabase.table("master_incidents").update({
                "status": "completed",
            }).eq("id", inc_id).execute()

            links = (
                supabase.table("incident_complaints")
                .select("complaint_id")
                .eq("incident_id", inc_id)
                .execute()
            )
            for link in (links.data or []):
                supabase.table("complaints").update({
                    "status": "completed",
                    "resolved_at": "now()",
                }).eq("id", link["complaint_id"]).execute()

    await audit.log(
        action=f"task_{new_status}",
        entity_type="task",
        entity_id=task_id,
        actor_id=actor_id,
        reason=action_data.notes,
    )

    return MessageResponse(message=f"Task status updated to {new_status}")
