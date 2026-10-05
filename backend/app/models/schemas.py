"""
Janseva AI — Pydantic Schemas
Request/response models for all API endpoints.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Union, Any
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class ComplaintStatus(str, Enum):
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    CLASSIFIED = "classified"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CLOSED = "closed"
    REOPENED = "reopened"
    REJECTED = "rejected"
    HUMAN_REVIEW = "human_review"


class IncidentStatus(str, Enum):
    OPEN = "open"
    TRIAGED = "triaged"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CLOSED = "closed"
    REOPENED = "reopened"


class TaskStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"


class WorkerStatus(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    ON_BREAK = "on_break"
    OFFLINE = "offline"
    ON_LEAVE = "on_leave"
    UNAVAILABLE = "unavailable"


class PriorityLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"


class ConfirmationStatus(str, Enum):
    YES = "yes"
    PARTIALLY = "partially"
    NO = "no"


class AssignmentStatus(str, Enum):
    RECOMMENDED = "recommended"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# =============================================================================
# AUTH SCHEMAS
# =============================================================================

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2)
    phone: Optional[str] = None
    role: str = "citizen"
    municipality_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict


class ProfileResponse(BaseModel):
    id: str
    email: str
    role: str
    full_name: str
    phone: Optional[str] = None
    municipality_id: Optional[str] = None
    department_id: Optional[str] = None
    ward_id: Optional[str] = None
    preferred_language: str = "en"
    created_at: Optional[str] = None


# =============================================================================
# LOCATION SCHEMAS
# =============================================================================

class LocationInput(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy: Optional[float] = None
    source: str = "gps"
    address: Optional[str] = None
    landmark: Optional[str] = None


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    source: str
    address: Optional[str] = None
    landmark: Optional[str] = None
    ward_id: Optional[str] = None
    geocoded_address: Optional[str] = None


# =============================================================================
# COMPLAINT SCHEMAS
# =============================================================================

class ComplaintCreate(BaseModel):
    """Citizen complaint submission."""
    text: Optional[str] = None
    description: Optional[str] = None
    voice_url: Optional[str] = None
    image_urls: Optional[List[str]] = None
    media_urls: Optional[List[str]] = None
    location: Optional[LocationInput] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    ward: Optional[str] = None
    citizen_name: Optional[str] = None
    citizen_phone: Optional[str] = None
    language: Optional[str] = None
    translated_text: Optional[str] = None


class TranslateRequest(BaseModel):
    """Text translation request."""
    text: str
    target_lang: Optional[str] = "en"


class AIClassification(BaseModel):
    """Structured AI classification result."""
    language: str = "en"
    category: str
    subcategory: Optional[str] = None
    department_code: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.MODERATE
    urgency: str = "normal"
    summary: str
    required_skills: List[str] = []
    required_equipment: List[str] = []
    safety_risk: bool = False
    estimated_affected_population: Optional[int] = None
    potential_risks: List[str] = []
    confidence: float = Field(ge=0, le=1)
    duration_reported: Optional[str] = None


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    complaint_number: str
    tracking_id: Optional[str] = None
    status: Union[ComplaintStatus, str] = "submitted"
    category: Optional[str] = None
    original_text: Optional[str] = None
    translated_text: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_category: Optional[str] = None
    ai_subcategory: Optional[str] = None
    ai_severity: Optional[str] = None
    priority_level: Optional[str] = None
    priority_score: Optional[float] = None
    priority_reasons: Optional[List[str]] = None
    location: Optional[LocationResponse] = None
    master_incident_id: Optional[str] = None
    submitted_at: Optional[Union[str, datetime]] = None
    classified_at: Optional[Union[str, datetime]] = None
    resolved_at: Optional[Union[str, datetime]] = None
    created_at: Optional[Union[str, datetime]] = None


class ComplaintListResponse(BaseModel):
    complaints: List[ComplaintResponse]
    total: int
    page: int
    page_size: int


class IncidentCreateInput(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = "Roads & Infrastructure"
    subcategory: Optional[str] = None
    department_id: Optional[str] = None
    priority_level: Optional[str] = "medium"
    priority_score: Optional[float] = 50.0
    status: Optional[str] = "open"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    ward_id: Optional[str] = None
    safety_risk: bool = False
    estimated_affected_population: Optional[int] = None


class IncidentUpdateInput(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    department_id: Optional[str] = None
    priority_level: Optional[str] = None
    priority_score: Optional[float] = None
    status: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    ward_id: Optional[str] = None
    safety_risk: Optional[bool] = None
    estimated_affected_population: Optional[int] = None


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    incident_number: str
    title: str
    description: Optional[str] = None
    status: Union[IncidentStatus, str] = "open"
    category: Optional[str] = None
    subcategory: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    priority_level: Optional[str] = None
    priority_score: Optional[float] = None
    priority_reasons: Optional[List[str]] = None
    complaint_count: int = 0
    severity: Optional[str] = None
    safety_risk: bool = False
    estimated_affected_population: Optional[int] = None
    ward_id: Optional[str] = None
    sla_deadline: Optional[Union[str, datetime]] = None
    sla_breached: bool = False
    location: Optional[LocationResponse] = None
    opened_at: Optional[Union[str, datetime]] = None
    created_at: Optional[Union[str, datetime]] = None


class IncidentListResponse(BaseModel):
    incidents: List[IncidentResponse]
    total: int
    page: int
    page_size: int


# =============================================================================
# WORKER SCHEMAS
# =============================================================================

class WorkerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: str
    full_name: Optional[str] = None
    employee_code: Optional[str] = None
    department_id: str
    department_name: Optional[str] = None
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    status: Union[WorkerStatus, str] = "available"
    skills: List[str] = []
    current_task_count: int = 0
    max_concurrent_tasks: int = 3
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class WorkerStatusUpdate(BaseModel):
    status: WorkerStatus
    reason: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class WorkerLocationUpdate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


# =============================================================================
# TASK & ASSIGNMENT SCHEMAS
# =============================================================================

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    task_number: str
    incident_id: str
    title: str
    description: Optional[str] = None
    status: Union[TaskStatus, str] = "pending"
    priority_level: Optional[str] = None
    required_skills: Optional[List[str]] = None
    required_equipment: Optional[List[str]] = None
    required_worker_count: int = 1
    estimated_duration_minutes: Optional[int] = None
    sla_deadline: Optional[Union[str, datetime]] = None
    location: Optional[LocationResponse] = None
    incident: Optional[IncidentResponse] = None
    assignments: Optional[List[dict]] = None
    started_at: Optional[Union[str, datetime]] = None
    completed_at: Optional[Union[str, datetime]] = None
    created_at: Optional[Union[str, datetime]] = None


class TaskAction(BaseModel):
    action: str = Field(description="accept, reject, start, pause, complete, report_blocker")
    reason: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ResourceCandidate(BaseModel):
    """A candidate worker/team for assignment."""
    worker_id: str
    worker_name: str
    team_id: Optional[str] = None
    team_name: Optional[str] = None
    skill_match_score: float
    distance_km: float
    workload_score: float
    overall_score: float
    reasons: List[str]
    equipment_available: bool
    estimated_arrival_minutes: Optional[float] = None


class AssignmentRecommendation(BaseModel):
    task_id: str
    candidates: List[ResourceCandidate]
    recommended_candidate_id: str
    recommendation_reasons: List[str]


class AssignmentApproval(BaseModel):
    assignment_id: str
    approved: bool
    reason: Optional[str] = None


class IncidentAssignRequest(BaseModel):
    worker_id: str
    notes: Optional[str] = None


class TaskStatusUpdateRequest(BaseModel):
    status: Optional[str] = None
    action: Optional[str] = None
    notes: Optional[str] = None
    evidence_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# =============================================================================
# ROUTE SCHEMAS
# =============================================================================

class RouteResponse(BaseModel):
    distance_meters: float
    duration_seconds: float
    geometry: Optional[dict] = None
    waypoints: Optional[List[dict]] = None


# =============================================================================
# DASHBOARD / ANALYTICS SCHEMAS
# =============================================================================

class DashboardMetrics(BaseModel):
    """All metrics computed from real database queries."""
    active_incidents: int = 0
    open_complaints: int = 0
    total_complaints: int = 0
    assigned_tasks: int = 0
    completed_today: int = 0
    avg_response_time_minutes: Optional[float] = None
    avg_resolution_time_minutes: Optional[float] = None
    sla_compliance_percent: Optional[float] = None
    reopened_complaints: int = 0
    available_workers: int = 0
    total_workers: int = 0
    pending_review: int = 0


class DepartmentMetric(BaseModel):
    department_id: str
    department_name: str
    open_incidents: int = 0
    total_complaints: int = 0
    avg_resolution_minutes: Optional[float] = None
    sla_compliance: Optional[float] = None


class WardMetric(BaseModel):
    ward_id: str
    ward_name: str
    ward_number: int
    complaint_count: int = 0
    open_incidents: int = 0


# =============================================================================
# NOTIFICATION SCHEMAS
# =============================================================================

class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    event_type: str
    status: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    read_at: Optional[str] = None
    created_at: Optional[str] = None


# =============================================================================
# ADMIN SCHEMAS
# =============================================================================

class DepartmentCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None
    municipality_id: str


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class CategoryCreate(BaseModel):
    department_id: str
    name: str
    code: str
    description: Optional[str] = None


class SkillCreate(BaseModel):
    name: str
    description: Optional[str] = None
    department_id: Optional[str] = None


class TeamCreate(BaseModel):
    department_id: str
    name: str
    supervisor_id: Optional[str] = None
    ward_id: Optional[str] = None


class VehicleCreate(BaseModel):
    department_id: str
    registration_number: str
    vehicle_type: str
    capacity: Optional[dict] = None


class EquipmentCreate(BaseModel):
    department_id: str
    name: str
    equipment_type: str
    quantity_total: int = 1


class WardCreate(BaseModel):
    municipality_id: str
    name: str
    number: int
    population: Optional[int] = None


class MunicipalityCreate(BaseModel):
    name: str
    code: str
    state: str
    district: Optional[str] = None


class SLAPolicyCreate(BaseModel):
    municipality_id: str
    department_id: Optional[str] = None
    category: Optional[str] = None
    priority_level: Optional[PriorityLevel] = None
    response_time_minutes: int
    resolution_time_minutes: int
    escalation_time_minutes: Optional[int] = None


class WorkerCreate(BaseModel):
    """Admin creating/registering a worker."""
    email: str
    password: str = Field(min_length=8)
    full_name: str
    phone: Optional[str] = None
    department_id: str
    team_id: Optional[str] = None
    employee_code: Optional[str] = None
    skill_ids: List[str] = []
    municipality_id: str


# =============================================================================
# CONFIRMATION SCHEMAS
# =============================================================================

class CitizenConfirmationCreate(BaseModel):
    complaint_id: str
    status: ConfirmationStatus
    feedback: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)


# =============================================================================
# GENERIC
# =============================================================================

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    services: dict


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
