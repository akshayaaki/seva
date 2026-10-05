"""
Janseva AI — Complaint Routes
Citizen complaint submission, AI classification, and tracking.
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, UploadFile, File
from typing import Optional, List
from app.auth import get_current_user, get_optional_user, require_citizen, CurrentUser, UserRole
from app.database import get_supabase_admin
from app.models.schemas import (
    ComplaintCreate, ComplaintResponse, ComplaintListResponse,
    LocationInput, CitizenConfirmationCreate, MessageResponse,
    TranslateRequest
)
from app.services.ai.classification import get_ai_service
from app.services.priority.engine import get_priority_engine, parse_duration_to_days
from app.services.geocoding.nominatim import get_geocoding_service
from app.services.clustering.engine import get_clustering_engine
from app.services.notifications.service import get_notification_service
from app.services.audit import get_audit_service
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


@router.post("/translate", response_model=dict)
async def translate_complaint_text(
    payload: TranslateRequest,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Translate grievance description into English."""
    ai = get_ai_service()
    result = await ai.translate_text(payload.text, payload.target_lang or "en")
    return result


async def _process_complaint(complaint_id: str, text: str, image_urls: list, citizen_user_id: str):
    """Background task: AI classify → prioritize → cluster → notify."""
    supabase = get_supabase_admin()
    ai = get_ai_service()
    priority_engine = get_priority_engine()
    clustering = get_clustering_engine()
    notifications = get_notification_service()
    audit = get_audit_service()

    try:
        # Update status to processing
        supabase.table("complaints").update({
            "status": "processing",
        }).eq("id", complaint_id).execute()

        # AI Classification
        classification = await ai.classify_complaint(
            text=text,
            image_urls=image_urls,
        )

        # Resolve department ID from code
        department_id = None
        if classification.department_code:
            dept_response = (
                supabase.table("departments")
                .select("id")
                .eq("code", classification.department_code)
                .limit(1)
                .execute()
            )
            if dept_response.data:
                department_id = dept_response.data[0]["id"]

        # Get complaint's location and municipality
        complaint = (
            supabase.table("complaints")
            .select("*, locations(*)")
            .eq("id", complaint_id)
            .single()
            .execute()
        )
        complaint_data = complaint.data
        municipality_id = complaint_data.get("municipality_id")
        ward_id = complaint_data.get("ward_id")
        latitude = None
        longitude = None
        location_id = None

        if complaint_data.get("locations"):
            loc = complaint_data["locations"]
            latitude = loc.get("latitude")
            longitude = loc.get("longitude")
            location_id = loc.get("id")

        # Priority Calculation
        duration_days = parse_duration_to_days(classification.duration_reported)
        priority = priority_engine.calculate(
            safety_risk=classification.safety_risk,
            severity=classification.severity,
            estimated_affected_population=classification.estimated_affected_population,
            duration_days=duration_days,
        )

        # Update complaint with classification
        update_data = {
            "status": "classified",
            "ai_category": classification.category,
            "ai_subcategory": classification.subcategory,
            "ai_severity": classification.severity.value if classification.severity else None,
            "ai_summary": classification.summary,
            "ai_department_id": department_id,
            "ai_confidence": classification.confidence,
            "ai_classification": {
                "language": classification.language,
                "urgency": classification.urgency,
                "required_skills": classification.required_skills,
                "required_equipment": classification.required_equipment,
                "potential_risks": classification.potential_risks,
                "estimated_affected_population": classification.estimated_affected_population,
                "duration_reported": classification.duration_reported,
            },
            "translated_text": classification.summary,
            "original_language": classification.language,
            "priority_score": priority["priority_score"],
            "priority_level": priority["priority_level"].value,
            "priority_reasons": priority["reason_codes"],
            "classified_at": "now()",
        }

        # If AI confidence is low, route to human review
        if classification.confidence < 0.5:
            update_data["status"] = "human_review"

        supabase.table("complaints").update(update_data).eq("id", complaint_id).execute()

        # Audit log
        await audit.log(
            action="complaint_classified",
            entity_type="complaint",
            entity_id=complaint_id,
            new_value={
                "category": classification.category,
                "severity": classification.severity.value if classification.severity else None,
                "confidence": classification.confidence,
                "priority_score": priority["priority_score"],
            },
        )

        # Incident Clustering
        matching_incident = await clustering.find_matching_incident(
            complaint_id=complaint_id,
            category=classification.category,
            latitude=latitude,
            longitude=longitude,
            summary=classification.summary,
            municipality_id=municipality_id,
        )

        if matching_incident:
            await clustering.add_to_incident(
                complaint_id=complaint_id,
                incident_id=matching_incident,
                similarity_score=0.7,
            )
        else:
            await clustering.create_incident(
                complaint_id=complaint_id,
                title=classification.summary,
                description=text,
                category=classification.category,
                subcategory=classification.subcategory,
                department_id=department_id,
                location_id=location_id,
                latitude=latitude,
                longitude=longitude,
                severity=classification.severity.value if classification.severity else None,
                safety_risk=classification.safety_risk,
                estimated_affected=classification.estimated_affected_population,
                municipality_id=municipality_id,
                ward_id=ward_id,
                priority_score=priority["priority_score"],
                priority_level=priority["priority_level"].value,
                priority_reasons=priority["reason_codes"],
            )

        # Notify citizen
        await notifications.notify_complaint_classified(
            citizen_user_id=citizen_user_id,
            complaint_id=complaint_id,
            category=classification.category,
        )

        logger.info(
            "complaint_processed",
            complaint_id=complaint_id,
            category=classification.category,
            priority=priority["priority_level"].value,
        )

    except Exception as e:
        logger.error("complaint_processing_error", complaint_id=complaint_id, error=str(e))
        # Mark as needing human review on error
        supabase.table("complaints").update({
            "status": "human_review",
        }).eq("id", complaint_id).execute()


@router.post("/", response_model=ComplaintResponse, status_code=201)
@router.post("", response_model=ComplaintResponse, status_code=201, include_in_schema=False)
async def create_complaint(
    complaint: ComplaintCreate,
    background_tasks: BackgroundTasks,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """
    Submit a new citizen complaint.
    Triggers background AI classification, prioritization, and clustering.
    """
    import uuid as _uuid
    import random
    from datetime import datetime

    supabase = get_supabase_admin()
    geocoding = get_geocoding_service()
    notifications = get_notification_service()
    audit = get_audit_service()

    complaint_text = complaint.text or complaint.description
    complaint_images = complaint.image_urls or complaint.media_urls or []

    if not complaint_text and not complaint.voice_url:
        raise HTTPException(
            status_code=400,
            detail="Please provide complaint text or a voice recording",
        )

    # Get citizen record if authenticated
    citizen_id = None
    if current_user:
        try:
            citizen_response = (
                supabase.table("citizens")
                .select("id")
                .eq("user_id", current_user.id)
                .execute()
            )
            if citizen_response.data and len(citizen_response.data) > 0:
                citizen_id = citizen_response.data[0]["id"]
        except Exception as e:
            logger.warn("citizen_lookup_error", error=str(e))

    # Process location
    location_id = None
    location_input = complaint.location
    if not location_input and complaint.latitude is not None and complaint.longitude is not None:
        location_input = LocationInput(
            latitude=complaint.latitude,
            longitude=complaint.longitude,
            address=complaint.address,
            landmark=complaint.ward,
            source="gps",
        )

    if location_input:
        try:
            # Reverse geocode to get address
            geo_result = await geocoding.reverse_geocode(
                location_input.latitude, location_input.longitude
            )

            source_clean = location_input.source if location_input.source in ("gps", "map", "manual", "voice") else "gps"
            location_data = {
                "latitude": location_input.latitude,
                "longitude": location_input.longitude,
                "accuracy": location_input.accuracy or 10.0,
                "source": source_clean,
                "address": location_input.address or (geo_result.get("display_name") if geo_result else "Mumbai"),
                "landmark": location_input.landmark or complaint.ward,
                "coordinates": f"POINT({location_input.longitude} {location_input.latitude})",
                "geocoded_address": geo_result.get("display_name") if geo_result else None,
            }

            loc_response = supabase.table("locations").insert(location_data).execute()
            if loc_response.data:
                location_id = loc_response.data[0]["id"]
        except Exception as e:
            logger.warn("location_insert_warning", error=str(e))

    municipality_id = current_user.municipality_id if current_user else None

    # Validate ward_id UUID
    clean_ward_id = None
    raw_ward = complaint.ward or (current_user.ward_id if current_user else None)
    if raw_ward:
        try:
            _uuid.UUID(str(raw_ward))
            clean_ward_id = str(raw_ward)
        except ValueError:
            clean_ward_id = None

    # Generate unique complaint reference number
    comp_number = f"JAN-{datetime.utcnow().year}-{random.randint(100000, 999999)}"

    # Create complaint record
    complaint_data = {
        "complaint_number": comp_number,
        "citizen_id": citizen_id,
        "status": "submitted",
        "original_text": complaint_text,
        "original_language": complaint.language or "en",
        "original_voice_url": complaint.voice_url,
        "original_image_urls": complaint_images,
        "location_id": location_id,
        "municipality_id": municipality_id,
        "ward_id": clean_ward_id,
    }

    response = supabase.table("complaints").insert(complaint_data).execute()
    created = response.data[0] if response.data else complaint_data
    if "id" not in created:
        created["id"] = str(_uuid.uuid4())
    if "complaint_number" not in created:
        created["complaint_number"] = comp_number

    # Audit log
    try:
        await audit.log(
            action="complaint_created",
            entity_type="complaint",
            entity_id=created["id"],
            actor_id=current_user.id if current_user else None,
            actor_role=current_user.role.value if current_user else "citizen",
        )
    except Exception:
        pass

    # Notify citizen of registration if authenticated
    if current_user:
        try:
            await notifications.notify_complaint_registered(
                citizen_user_id=current_user.id,
                complaint_id=created["id"],
                complaint_number=created["complaint_number"],
            )
        except Exception:
            pass

    # Trigger background processing
    if complaint_text:
        try:
            background_tasks.add_task(
                _process_complaint,
                complaint_id=created["id"],
                text=complaint_text,
                image_urls=complaint_images,
                citizen_user_id=current_user.id if current_user else None,
            )
        except Exception as e:
            logger.warn("background_task_dispatch_warning", error=str(e))

    return ComplaintResponse(
        id=created["id"],
        complaint_number=created["complaint_number"],
        tracking_id=created["complaint_number"],
        status=created["status"],
        category=created.get("ai_category") or "Civic Grievance",
        original_text=created.get("original_text"),
        submitted_at=created.get("submitted_at") or datetime.utcnow().isoformat(),
        created_at=created.get("created_at") or datetime.utcnow().isoformat(),
    )


@router.get("/", response_model=ComplaintListResponse)
async def list_complaints(
    current_user: CurrentUser = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
):
    """List complaints. Citizens see their own; officials see department/all."""
    supabase = get_supabase_admin()

    query = supabase.table("complaints").select("*, locations(*)", count="exact")

    # RBAC filtering
    if current_user.role == UserRole.CITIZEN:
        citizen = (
            supabase.table("citizens")
            .select("id")
            .eq("user_id", current_user.id)
            .single()
            .execute()
        )
        if citizen.data:
            query = query.eq("citizen_id", citizen.data["id"])
        else:
            return ComplaintListResponse(complaints=[], total=0, page=page, page_size=page_size)
    elif current_user.role == UserRole.WORKER:
        # Workers see complaints linked to their assigned tasks
        pass  # For now, allow read
    elif current_user.role in (UserRole.DEPARTMENT_OFFICER, UserRole.SUPERVISOR):
        if current_user.department_id:
            query = query.eq("ai_department_id", current_user.department_id)

    if status:
        query = query.eq("status", status)

    # Pagination
    offset = (page - 1) * page_size
    query = query.order("created_at", desc=True).range(offset, offset + page_size - 1)

    response = query.execute()
    complaints = response.data or []
    total = response.count or 0

    results = []
    for c in complaints:
        loc = None
        if c.get("locations"):
            loc_data = c["locations"]
            from app.models.schemas import LocationResponse
            loc = LocationResponse(
                id=loc_data["id"],
                latitude=loc_data["latitude"],
                longitude=loc_data["longitude"],
                accuracy=loc_data.get("accuracy"),
                source=loc_data.get("source", "unknown"),
                address=loc_data.get("address"),
                geocoded_address=loc_data.get("geocoded_address"),
            )

        results.append(ComplaintResponse(
            id=c["id"],
            complaint_number=c["complaint_number"],
            status=c["status"],
            original_text=c.get("original_text"),
            translated_text=c.get("translated_text"),
            ai_summary=c.get("ai_summary"),
            ai_category=c.get("ai_category"),
            ai_subcategory=c.get("ai_subcategory"),
            ai_severity=c.get("ai_severity"),
            priority_level=c.get("priority_level"),
            priority_score=c.get("priority_score"),
            priority_reasons=c.get("priority_reasons"),
            location=loc,
            master_incident_id=c.get("master_incident_id"),
            submitted_at=c.get("submitted_at"),
            classified_at=c.get("classified_at"),
            resolved_at=c.get("resolved_at"),
            created_at=c.get("created_at"),
        ))

    return ComplaintListResponse(
        complaints=results,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{complaint_id}", response_model=ComplaintResponse)
async def get_complaint(
    complaint_id: str,
    current_user: Optional[CurrentUser] = Depends(get_optional_user),
):
    """Get a specific complaint or incident by ID or tracking code."""
    import uuid as _uuid
    supabase = get_supabase_admin()
    clean_id = complaint_id.strip()

    is_uuid = False
    try:
        _uuid.UUID(clean_id)
        is_uuid = True
    except ValueError:
        is_uuid = False

    response = None

    # 1. If UUID, query by complaint id
    if is_uuid:
        response = (
            supabase.table("complaints")
            .select("*, locations(*)")
            .eq("id", clean_id)
            .single()
            .execute()
        )

    # 2. If not found or not UUID, query by complaint_number
    if not response or not response.data:
        response = (
            supabase.table("complaints")
            .select("*, locations(*)")
            .eq("complaint_number", clean_id.upper())
            .single()
            .execute()
        )

    if not response or not response.data:
        response = (
            supabase.table("complaints")
            .select("*, locations(*)")
            .eq("complaint_number", clean_id)
            .single()
            .execute()
        )

    # 3. If still not found, check if it's an Incident Number (e.g. INC-...)
    if not response or not response.data:
        inc_res = None
        if is_uuid:
            inc_res = (
                supabase.table("master_incidents")
                .select("*, locations(*)")
                .eq("id", clean_id)
                .single()
                .execute()
            )
        if not inc_res or not inc_res.data:
            inc_res = (
                supabase.table("master_incidents")
                .select("*, locations(*)")
                .eq("incident_number", clean_id.upper())
                .single()
                .execute()
            )
        if not inc_res or not inc_res.data:
            inc_res = (
                supabase.table("master_incidents")
                .select("*, locations(*)")
                .eq("incident_number", clean_id)
                .single()
                .execute()
            )

        if inc_res and inc_res.data:
            inc = inc_res.data
            loc = None
            if inc.get("locations"):
                loc_data = inc["locations"]
                from app.models.schemas import LocationResponse
                loc = LocationResponse(
                    id=loc_data["id"],
                    latitude=loc_data["latitude"],
                    longitude=loc_data["longitude"],
                    accuracy=loc_data.get("accuracy"),
                    source=loc_data.get("source", "unknown"),
                    address=loc_data.get("address"),
                    geocoded_address=loc_data.get("geocoded_address"),
                )

            return ComplaintResponse(
                id=inc["id"],
                complaint_number=inc["incident_number"],
                status=inc["status"],
                original_text=inc.get("description") or inc.get("title"),
                translated_text=inc.get("description") or inc.get("title"),
                ai_summary=inc.get("description") or inc.get("title"),
                ai_category=inc.get("category"),
                ai_subcategory=inc.get("subcategory"),
                ai_severity=inc.get("severity"),
                priority_level=inc.get("priority_level"),
                priority_score=inc.get("priority_score"),
                priority_reasons=inc.get("priority_reasons"),
                location=loc,
                master_incident_id=inc["id"],
                submitted_at=inc.get("created_at"),
                created_at=inc.get("created_at"),
            )

    if not response or not response.data:
        raise HTTPException(
            status_code=404,
            detail=f"No grievance or incident found for Reference ID '{clean_id.upper()}'. Please check the code and try again."
        )

    c = response.data

    # RBAC check only when citizen is authenticated and trying to view another private citizen's ticket
    if current_user and current_user.role == UserRole.CITIZEN and c.get("citizen_id"):
        citizen = (
            supabase.table("citizens")
            .select("id")
            .eq("user_id", current_user.id)
            .single()
            .execute()
        )
        if citizen.data and citizen.data["id"] != c["citizen_id"]:
            raise HTTPException(status_code=403, detail="Access denied")

    loc = None
    if c.get("locations"):
        loc_data = c["locations"]
        from app.models.schemas import LocationResponse
        loc = LocationResponse(
            id=loc_data["id"],
            latitude=loc_data["latitude"],
            longitude=loc_data["longitude"],
            accuracy=loc_data.get("accuracy"),
            source=loc_data.get("source", "unknown"),
            address=loc_data.get("address"),
            geocoded_address=loc_data.get("geocoded_address"),
        )

    return ComplaintResponse(
        id=c["id"],
        complaint_number=c["complaint_number"],
        status=c["status"],
        original_text=c.get("original_text"),
        translated_text=c.get("translated_text"),
        ai_summary=c.get("ai_summary"),
        ai_category=c.get("ai_category"),
        ai_subcategory=c.get("ai_subcategory"),
        ai_severity=c.get("ai_severity"),
        priority_level=c.get("priority_level"),
        priority_score=c.get("priority_score"),
        priority_reasons=c.get("priority_reasons"),
        location=loc,
        master_incident_id=c.get("master_incident_id"),
        submitted_at=c.get("submitted_at"),
        classified_at=c.get("classified_at"),
        resolved_at=c.get("resolved_at"),
        created_at=c.get("created_at"),
    )


@router.post("/{complaint_id}/confirm", response_model=MessageResponse)
async def confirm_resolution(
    complaint_id: str,
    confirmation: CitizenConfirmationCreate,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Citizen confirms or rejects resolution."""
    supabase = get_supabase_admin()
    notifications = get_notification_service()
    audit = get_audit_service()

    # Get citizen record
    citizen = (
        supabase.table("citizens")
        .select("id")
        .eq("user_id", current_user.id)
        .single()
        .execute()
    )

    if not citizen.data:
        raise HTTPException(status_code=403, detail="Citizen record not found")

    # Store confirmation
    supabase.table("citizen_confirmations").insert({
        "complaint_id": complaint_id,
        "citizen_id": citizen.data["id"],
        "status": confirmation.status.value,
        "feedback": confirmation.feedback,
        "rating": confirmation.rating,
    }).execute()

    if confirmation.status.value == "no":
        # Reopen complaint and incident
        supabase.table("complaints").update({
            "status": "reopened",
            "resolved_at": None,
        }).eq("id", complaint_id).execute()

        # Get linked incident
        complaint = (
            supabase.table("complaints")
            .select("master_incident_id, complaint_number")
            .eq("id", complaint_id)
            .single()
            .execute()
        )

        if complaint.data and complaint.data.get("master_incident_id"):
            supabase.table("master_incidents").update({
                "status": "reopened",
            }).eq("id", complaint.data["master_incident_id"]).execute()

        await audit.log(
            action="complaint_reopened",
            entity_type="complaint",
            entity_id=complaint_id,
            actor_id=current_user.id,
            actor_role=current_user.role.value,
            reason=confirmation.feedback,
        )

        return MessageResponse(
            message="Complaint reopened. We will reassign your issue.",
        )

    elif confirmation.status.value == "yes":
        supabase.table("complaints").update({
            "status": "closed",
            "closed_at": "now()",
        }).eq("id", complaint_id).execute()

        await audit.log(
            action="complaint_closed",
            entity_type="complaint",
            entity_id=complaint_id,
            actor_id=current_user.id,
        )

        return MessageResponse(message="Thank you for confirming. Complaint closed.")

    return MessageResponse(message="Confirmation recorded.")


@router.post("/{complaint_id}/evidence")
async def upload_evidence(
    complaint_id: str,
    file: UploadFile = File(...),
    stage: str = "before",
    current_user: CurrentUser = Depends(get_current_user),
):
    """Upload evidence (photo/video) for a complaint."""
    supabase = get_supabase_admin()

    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/webp", "video/mp4", "audio/mpeg", "audio/wav"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not allowed")

    # Upload to Supabase Storage
    file_bytes = await file.read()
    file_path = f"evidence/{complaint_id}/{file.filename}"

    try:
        supabase.storage.from_("evidence").upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": file.content_type},
        )

        # Get public URL
        public_url = supabase.storage.from_("evidence").get_public_url(file_path)

        # Determine media type
        media_type = "image"
        if file.content_type and file.content_type.startswith("video"):
            media_type = "video"
        elif file.content_type and file.content_type.startswith("audio"):
            media_type = "audio"

        # Store evidence record
        supabase.table("complaint_evidence").insert({
            "complaint_id": complaint_id,
            "uploader_id": current_user.id,
            "media_type": media_type,
            "storage_path": file_path,
            "storage_url": public_url,
            "file_name": file.filename,
            "file_size": len(file_bytes),
            "mime_type": file.content_type,
            "stage": stage,
        }).execute()

        return {"message": "Evidence uploaded", "url": public_url}

    except Exception as e:
        logger.error("evidence_upload_error", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to upload evidence")
