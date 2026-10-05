"""
Janseva AI — Admin Routes
Department, team, worker, vehicle, equipment, ward management + analytics.
"""
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from typing import Optional
from app.auth import get_current_user, get_optional_user, require_admin, require_system_admin, CurrentUser
from app.database import get_supabase_admin
from app.models.schemas import (
    DepartmentCreate, DepartmentUpdate, CategoryCreate, SkillCreate,
    TeamCreate, VehicleCreate, EquipmentCreate, WardCreate,
    MunicipalityCreate, SLAPolicyCreate, WorkerCreate,
    DashboardMetrics, MessageResponse
)
from app.services.audit import get_audit_service
import structlog
import csv
import io

logger = structlog.get_logger()
router = APIRouter(prefix="/api/admin", tags=["Administration"])


# =============================================================================
# DASHBOARD METRICS (computed from real database)
# =============================================================================

@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard_metrics(
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """
    Get real dashboard metrics computed from the production database.
    Every number here is a real count/calculation — never hardcoded.
    """
    supabase = get_supabase_admin()
    municipality_id = current_user.municipality_id if current_user else None

    # Active incidents
    active_q = supabase.table("master_incidents").select("id", count="exact").in_(
        "status", ["open", "triaged", "assigned", "in_progress"]
    )
    if municipality_id:
        active_q = active_q.eq("municipality_id", municipality_id)
    active_incidents = active_q.execute().count or 0

    # Open complaints
    open_q = supabase.table("complaints").select("id", count="exact").in_(
        "status", ["submitted", "processing", "classified", "human_review"]
    )
    if municipality_id:
        open_q = open_q.eq("municipality_id", municipality_id)
    open_complaints = open_q.execute().count or 0

    # Total complaints
    total_q = supabase.table("complaints").select("id", count="exact")
    if municipality_id:
        total_q = total_q.eq("municipality_id", municipality_id)
    total_complaints = total_q.execute().count or 0

    # Assigned tasks
    assigned_tasks = (
        supabase.table("tasks")
        .select("id", count="exact")
        .in_("status", ["accepted", "in_progress"])
        .execute()
    ).count or 0

    # Completed today
    from datetime import datetime, timezone
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    completed_today = (
        supabase.table("tasks")
        .select("id", count="exact")
        .eq("status", "completed")
        .gte("completed_at", f"{today}T00:00:00Z")
        .execute()
    ).count or 0

    # Reopened complaints
    reopened = (
        supabase.table("complaints")
        .select("id", count="exact")
        .eq("status", "reopened")
        .execute()
    ).count or 0

    # Available workers
    available_workers = (
        supabase.table("workers")
        .select("id", count="exact")
        .eq("status", "available")
        .is_("deleted_at", "null")
        .execute()
    ).count or 0

    total_workers = (
        supabase.table("workers")
        .select("id", count="exact")
        .is_("deleted_at", "null")
        .execute()
    ).count or 0

    # Pending human review
    pending_review = (
        supabase.table("complaints")
        .select("id", count="exact")
        .eq("status", "human_review")
        .execute()
    ).count or 0

    # Average response time (from submitted to assigned, in minutes)
    avg_response = None
    avg_resolution = None
    sla_compliance = None

    # Compute from actual closed complaints with timestamps
    closed_complaints = (
        supabase.table("complaints")
        .select("submitted_at, assigned_at, resolved_at, closed_at")
        .eq("status", "closed")
        .limit(1000)
        .execute()
    )

    if closed_complaints.data:
        response_times = []
        resolution_times = []
        for c in closed_complaints.data:
            if c.get("submitted_at") and c.get("assigned_at"):
                try:
                    sub = datetime.fromisoformat(c["submitted_at"].replace("Z", "+00:00"))
                    asg = datetime.fromisoformat(c["assigned_at"].replace("Z", "+00:00"))
                    response_times.append((asg - sub).total_seconds() / 60)
                except (ValueError, TypeError):
                    pass
            if c.get("submitted_at") and c.get("resolved_at"):
                try:
                    sub = datetime.fromisoformat(c["submitted_at"].replace("Z", "+00:00"))
                    res = datetime.fromisoformat(c["resolved_at"].replace("Z", "+00:00"))
                    resolution_times.append((res - sub).total_seconds() / 60)
                except (ValueError, TypeError):
                    pass

        if response_times:
            avg_response = round(sum(response_times) / len(response_times), 1)
        if resolution_times:
            avg_resolution = round(sum(resolution_times) / len(resolution_times), 1)

    return DashboardMetrics(
        active_incidents=active_incidents,
        open_complaints=open_complaints,
        total_complaints=total_complaints,
        assigned_tasks=assigned_tasks,
        completed_today=completed_today,
        avg_response_time_minutes=avg_response,
        avg_resolution_time_minutes=avg_resolution,
        sla_compliance_percent=sla_compliance,
        reopened_complaints=reopened,
        available_workers=available_workers,
        total_workers=total_workers,
        pending_review=pending_review,
    )


# =============================================================================
# MUNICIPALITY
# =============================================================================

@router.post("/municipalities", response_model=dict)
async def create_municipality(
    data: MunicipalityCreate,
    current_user: CurrentUser = Depends(require_system_admin),
):
    supabase = get_supabase_admin()
    response = supabase.table("municipalities").insert(data.model_dump()).execute()
    return response.data[0]


@router.get("/municipalities")
async def list_municipalities(
    current_user: CurrentUser = Depends(require_admin),
):
    supabase = get_supabase_admin()
    response = supabase.table("municipalities").select("*").is_("deleted_at", "null").execute()
    return response.data or []


# =============================================================================
# DEPARTMENTS
# =============================================================================

@router.post("/departments", response_model=dict)
async def create_department(
    data: DepartmentCreate,
    current_user: CurrentUser = Depends(require_admin),
):
    supabase = get_supabase_admin()
    audit = get_audit_service()
    response = supabase.table("departments").insert(data.model_dump()).execute()
    await audit.log(
        action="department_created",
        entity_type="department",
        entity_id=response.data[0]["id"],
        actor_id=current_user.id,
    )
    return response.data[0]


@router.get("/departments")
async def list_departments(
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
    municipality_id: Optional[str] = None,
):
    supabase = get_supabase_admin()
    query = supabase.table("departments").select("*").is_("deleted_at", "null")
    mid = municipality_id or (current_user.municipality_id if current_user else None)
    if mid:
        query = query.eq("municipality_id", mid)
    response = query.execute()
    return response.data or []


@router.put("/departments/{dept_id}", response_model=dict)
async def update_department(
    dept_id: str,
    data: DepartmentUpdate,
    current_user: CurrentUser = Depends(require_admin),
):
    supabase = get_supabase_admin()
    update = {k: v for k, v in data.model_dump().items() if v is not None}
    response = supabase.table("departments").update(update).eq("id", dept_id).execute()
    return response.data[0] if response.data else {}


# =============================================================================
# CATEGORIES
# =============================================================================

@router.post("/categories", response_model=dict)
async def create_category(
    data: CategoryCreate,
    current_user: CurrentUser = Depends(require_admin),
):
    supabase = get_supabase_admin()
    response = supabase.table("department_categories").insert(data.model_dump()).execute()
    return response.data[0]


@router.get("/categories")
async def list_categories(
    department_id: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()
    query = supabase.table("department_categories").select("*, departments(name)")
    if department_id:
        query = query.eq("department_id", department_id)
    response = query.execute()
    return response.data or []


# =============================================================================
# SKILLS
# =============================================================================

@router.post("/skills", response_model=dict)
async def create_skill(data: SkillCreate, current_user: CurrentUser = Depends(require_admin)):
    supabase = get_supabase_admin()
    response = supabase.table("skills").insert(data.model_dump()).execute()
    return response.data[0]


@router.get("/skills")
async def list_skills(current_user: CurrentUser = Depends(get_current_user)):
    supabase = get_supabase_admin()
    response = supabase.table("skills").select("*").execute()
    return response.data or []


# =============================================================================
# TEAMS
# =============================================================================

@router.post("/teams", response_model=dict)
async def create_team(data: TeamCreate, current_user: CurrentUser = Depends(require_admin)):
    supabase = get_supabase_admin()
    response = supabase.table("teams").insert(data.model_dump()).execute()
    return response.data[0]


@router.get("/teams")
async def list_teams(
    department_id: Optional[str] = None,
    current_user: CurrentUser = Depends(require_admin),
):
    supabase = get_supabase_admin()
    query = supabase.table("teams").select("*, departments(name)").is_("deleted_at", "null")
    if department_id:
        query = query.eq("department_id", department_id)
    response = query.execute()
    return response.data or []


# =============================================================================
# WORKERS (Admin management)
# =============================================================================

@router.post("/workers", response_model=dict)
async def create_worker(
    data: WorkerCreate,
    current_user: CurrentUser = Depends(require_admin),
):
    """Admin creates a worker account."""
    supabase = get_supabase_admin()
    audit = get_audit_service()

    # Create auth user
    auth_response = supabase.auth.admin.create_user({
        "email": data.email,
        "password": data.password,
        "email_confirm": True,
    })

    if not auth_response.user:
        raise HTTPException(status_code=400, detail="Failed to create user account")

    user_id = auth_response.user.id

    # Create profile
    supabase.table("user_profiles").insert({
        "id": user_id,
        "role": "worker",
        "full_name": data.full_name,
        "phone": data.phone,
        "municipality_id": data.municipality_id,
        "department_id": data.department_id,
    }).execute()

    # Create worker record
    worker_response = supabase.table("workers").insert({
        "user_id": user_id,
        "department_id": data.department_id,
        "team_id": data.team_id,
        "employee_code": data.employee_code,
        "status": "offline",
    }).execute()

    worker_id = worker_response.data[0]["id"]

    # Assign skills
    for skill_id in data.skill_ids:
        supabase.table("worker_skills").insert({
            "worker_id": worker_id,
            "skill_id": skill_id,
        }).execute()

    await audit.log(
        action="worker_created",
        entity_type="worker",
        entity_id=worker_id,
        actor_id=current_user.id,
        new_value={"email": data.email, "department_id": data.department_id},
    )

    return {"id": worker_id, "user_id": user_id, "message": "Worker created successfully"}


@router.get("/workers")
async def list_workers(
    department_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    supabase = get_supabase_admin()
    query = (
        supabase.table("workers")
        .select("*, user_profiles(full_name, phone, email:id), departments(name), teams(name)")
        .is_("deleted_at", "null")
    )
    if department_id:
        query = query.eq("department_id", department_id)
    if status:
        query = query.eq("status", status)
    response = query.execute()
    return response.data or []


# =============================================================================
# VEHICLES & EQUIPMENT
# =============================================================================

@router.post("/vehicles", response_model=dict)
async def create_vehicle(data: VehicleCreate, current_user: CurrentUser = Depends(require_admin)):
    supabase = get_supabase_admin()
    response = supabase.table("vehicles").insert(data.model_dump()).execute()
    return response.data[0]


@router.get("/vehicles")
async def list_vehicles(department_id: Optional[str] = None, current_user: CurrentUser = Depends(require_admin)):
    supabase = get_supabase_admin()
    query = supabase.table("vehicles").select("*, departments(name)").is_("deleted_at", "null")
    if department_id:
        query = query.eq("department_id", department_id)
    response = query.execute()
    return response.data or []


@router.post("/equipment", response_model=dict)
async def create_equipment(data: EquipmentCreate, current_user: CurrentUser = Depends(require_admin)):
    supabase = get_supabase_admin()
    response = supabase.table("equipment").insert(data.model_dump()).execute()
    return response.data[0]


@router.get("/equipment")
async def list_equipment(department_id: Optional[str] = None, current_user: CurrentUser = Depends(require_admin)):
    supabase = get_supabase_admin()
    query = supabase.table("equipment").select("*, departments(name)").is_("deleted_at", "null")
    if department_id:
        query = query.eq("department_id", department_id)
    response = query.execute()
    return response.data or []


# =============================================================================
# WARDS
# =============================================================================

@router.post("/wards", response_model=dict)
async def create_ward(data: WardCreate, current_user: CurrentUser = Depends(require_admin)):
    supabase = get_supabase_admin()
    response = supabase.table("wards").insert(data.model_dump()).execute()
    return response.data[0]


@router.get("/wards")
async def list_wards(
    municipality_id: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    supabase = get_supabase_admin()
    query = supabase.table("wards").select("*").is_("deleted_at", "null")
    mid = municipality_id or current_user.municipality_id
    if mid:
        query = query.eq("municipality_id", mid)
    response = query.execute()
    return response.data or []


# =============================================================================
# SLA POLICIES
# =============================================================================

@router.post("/sla-policies", response_model=dict)
async def create_sla_policy(data: SLAPolicyCreate, current_user: CurrentUser = Depends(require_admin)):
    supabase = get_supabase_admin()
    dump = data.model_dump()
    if dump.get("priority_level"):
        dump["priority_level"] = dump["priority_level"].value
    response = supabase.table("sla_policies").insert(dump).execute()
    return response.data[0]


@router.get("/sla-policies")
async def list_sla_policies(current_user: CurrentUser = Depends(require_admin)):
    supabase = get_supabase_admin()
    response = supabase.table("sla_policies").select("*, departments(name)").eq("is_active", True).execute()
    return response.data or []


# =============================================================================
# CSV IMPORT
# =============================================================================

@router.post("/import/{entity_type}")
async def import_csv(
    entity_type: str,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_admin),
):
    """Import data from CSV. Validates before committing."""
    allowed_types = {"workers", "departments", "teams", "vehicles", "equipment", "wards", "skills"}
    if entity_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Cannot import '{entity_type}'")

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a CSV file")

    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    rows = list(reader)

    if not rows:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    supabase = get_supabase_admin()
    errors = []
    imported = 0

    for i, row in enumerate(rows):
        try:
            # Clean empty strings to None
            cleaned = {k: (v.strip() if v and v.strip() else None) for k, v in row.items()}

            if entity_type == "departments":
                if not cleaned.get("name") or not cleaned.get("code") or not cleaned.get("municipality_id"):
                    errors.append(f"Row {i+1}: name, code, and municipality_id are required")
                    continue
                supabase.table("departments").insert({
                    "name": cleaned["name"],
                    "code": cleaned["code"],
                    "description": cleaned.get("description"),
                    "municipality_id": cleaned["municipality_id"],
                }).execute()
            elif entity_type == "wards":
                if not cleaned.get("name") or not cleaned.get("number") or not cleaned.get("municipality_id"):
                    errors.append(f"Row {i+1}: name, number, and municipality_id are required")
                    continue
                supabase.table("wards").insert({
                    "name": cleaned["name"],
                    "number": int(cleaned["number"]),
                    "municipality_id": cleaned["municipality_id"],
                    "population": int(cleaned["population"]) if cleaned.get("population") else None,
                }).execute()
            elif entity_type == "skills":
                if not cleaned.get("name"):
                    errors.append(f"Row {i+1}: name is required")
                    continue
                supabase.table("skills").insert({
                    "name": cleaned["name"],
                    "description": cleaned.get("description"),
                    "department_id": cleaned.get("department_id"),
                }).execute()
            elif entity_type == "vehicles":
                if not cleaned.get("registration_number") or not cleaned.get("vehicle_type") or not cleaned.get("department_id"):
                    errors.append(f"Row {i+1}: registration_number, vehicle_type, department_id required")
                    continue
                supabase.table("vehicles").insert({
                    "registration_number": cleaned["registration_number"],
                    "vehicle_type": cleaned["vehicle_type"],
                    "department_id": cleaned["department_id"],
                }).execute()
            elif entity_type == "equipment":
                if not cleaned.get("name") or not cleaned.get("equipment_type") or not cleaned.get("department_id"):
                    errors.append(f"Row {i+1}: name, equipment_type, department_id required")
                    continue
                supabase.table("equipment").insert({
                    "name": cleaned["name"],
                    "equipment_type": cleaned["equipment_type"],
                    "department_id": cleaned["department_id"],
                    "quantity_total": int(cleaned.get("quantity_total", "1")),
                    "quantity_available": int(cleaned.get("quantity_available", "1")),
                }).execute()

            imported += 1

        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")

    return {
        "imported": imported,
        "errors": errors,
        "total_rows": len(rows),
    }


# =============================================================================
# NOTIFICATIONS
# =============================================================================

@router.get("/notifications")
async def get_notifications(
    current_user: CurrentUser = Depends(get_current_user),
    unread_only: bool = False,
    limit: int = Query(50, ge=1, le=200),
):
    from app.services.notifications.service import get_notification_service
    notifications = get_notification_service()
    return await notifications.get_user_notifications(
        user_id=current_user.id,
        limit=limit,
        unread_only=unread_only,
    )


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    from app.services.notifications.service import get_notification_service
    notifications = get_notification_service()
    await notifications.mark_as_read(notification_id, current_user.id)
    return {"message": "Marked as read"}


# =============================================================================
# AUDIT LOGS
# =============================================================================

@router.get("/audit-logs")
async def get_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    audit = get_audit_service()
    return await audit.get_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )
