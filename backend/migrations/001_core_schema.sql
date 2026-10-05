-- =============================================================================
-- Janseva AI — Database Migration 001: Core Schema
-- =============================================================================
-- Run this against your Supabase project via the SQL Editor.
-- This creates all core tables with PostGIS support, constraints, and indexes.
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- =============================================================================
-- ENUM TYPES
-- =============================================================================

CREATE TYPE user_role AS ENUM (
    'citizen', 'worker', 'supervisor', 'department_officer',
    'municipal_admin', 'system_admin'
);

CREATE TYPE complaint_status AS ENUM (
    'submitted', 'processing', 'classified', 'assigned',
    'in_progress', 'completed', 'verified', 'closed', 'reopened',
    'rejected', 'human_review'
);

CREATE TYPE incident_status AS ENUM (
    'open', 'triaged', 'assigned', 'in_progress',
    'completed', 'verified', 'closed', 'reopened'
);

CREATE TYPE task_status AS ENUM (
    'pending', 'accepted', 'rejected', 'in_progress',
    'paused', 'blocked', 'completed', 'verified', 'cancelled'
);

CREATE TYPE worker_status AS ENUM (
    'available', 'busy', 'on_break', 'offline', 'on_leave', 'unavailable'
);

CREATE TYPE priority_level AS ENUM (
    'critical', 'high', 'medium', 'low'
);

CREATE TYPE severity_level AS ENUM (
    'critical', 'major', 'moderate', 'minor'
);

CREATE TYPE notification_channel AS ENUM (
    'push', 'email', 'sms', 'whatsapp', 'in_app'
);

CREATE TYPE notification_status AS ENUM (
    'pending', 'sent', 'delivered', 'failed', 'read'
);

CREATE TYPE job_status AS ENUM (
    'queued', 'processing', 'completed', 'failed'
);

CREATE TYPE media_type AS ENUM (
    'image', 'video', 'audio', 'document'
);

CREATE TYPE location_source AS ENUM (
    'gps', 'map_selection', 'address', 'landmark', 'manual', 'geocoded'
);

CREATE TYPE evidence_stage AS ENUM (
    'before', 'during', 'after'
);

CREATE TYPE confirmation_status AS ENUM (
    'yes', 'partially', 'no'
);

CREATE TYPE assignment_status AS ENUM (
    'recommended', 'approved', 'rejected', 'active', 'completed', 'cancelled'
);

CREATE TYPE vehicle_status AS ENUM (
    'available', 'in_use', 'maintenance', 'decommissioned'
);

CREATE TYPE equipment_status AS ENUM (
    'available', 'in_use', 'maintenance', 'decommissioned'
);

-- =============================================================================
-- CORE TABLES
-- =============================================================================

-- ── Municipalities ──────────────────────────────────────────────────────────
CREATE TABLE municipalities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    state TEXT NOT NULL,
    district TEXT,
    boundary GEOMETRY(MultiPolygon, 4326),
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- ── Wards ───────────────────────────────────────────────────────────────────
CREATE TABLE wards (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipality_id UUID NOT NULL REFERENCES municipalities(id),
    name TEXT NOT NULL,
    number INTEGER NOT NULL,
    boundary GEOMETRY(MultiPolygon, 4326),
    population INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(municipality_id, number)
);

-- ── Departments ─────────────────────────────────────────────────────────────
CREATE TABLE departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipality_id UUID NOT NULL REFERENCES municipalities(id),
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT,
    head_user_id UUID,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,
    UNIQUE(municipality_id, code)
);

-- ── Department Categories ───────────────────────────────────────────────────
CREATE TABLE department_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID NOT NULL REFERENCES departments(id),
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(department_id, code)
);

-- ── Department Subcategories ────────────────────────────────────────────────
CREATE TABLE department_subcategories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID NOT NULL REFERENCES department_categories(id),
    name TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category_id, code)
);

-- ── Skills ──────────────────────────────────────────────────────────────────
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    department_id UUID REFERENCES departments(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Department Required Skills ──────────────────────────────────────────────
CREATE TABLE department_skills (
    department_id UUID NOT NULL REFERENCES departments(id),
    skill_id UUID NOT NULL REFERENCES skills(id),
    PRIMARY KEY (department_id, skill_id)
);

-- ── User Profiles ───────────────────────────────────────────────────────────
-- Extends Supabase auth.users
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role NOT NULL DEFAULT 'citizen',
    full_name TEXT NOT NULL,
    phone TEXT,
    avatar_url TEXT,
    municipality_id UUID REFERENCES municipalities(id),
    ward_id UUID REFERENCES wards(id),
    department_id UUID REFERENCES departments(id),
    preferred_language TEXT DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- ── Citizens ────────────────────────────────────────────────────────────────
CREATE TABLE citizens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES user_profiles(id),
    address TEXT,
    location GEOMETRY(Point, 4326),
    notification_preferences JSONB DEFAULT '{"email": true, "push": true, "sms": false}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Teams ───────────────────────────────────────────────────────────────────
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID NOT NULL REFERENCES departments(id),
    name TEXT NOT NULL,
    supervisor_id UUID REFERENCES user_profiles(id),
    ward_id UUID REFERENCES wards(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- ── Workers ─────────────────────────────────────────────────────────────────
CREATE TABLE workers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES user_profiles(id),
    department_id UUID NOT NULL REFERENCES departments(id),
    team_id UUID REFERENCES teams(id),
    employee_code TEXT UNIQUE,
    status worker_status DEFAULT 'offline',
    current_location GEOMETRY(Point, 4326),
    current_location_updated_at TIMESTAMPTZ,
    max_concurrent_tasks INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- ── Worker Skills ───────────────────────────────────────────────────────────
CREATE TABLE worker_skills (
    worker_id UUID NOT NULL REFERENCES workers(id),
    skill_id UUID NOT NULL REFERENCES skills(id),
    proficiency_level INTEGER DEFAULT 1 CHECK (proficiency_level BETWEEN 1 AND 5),
    PRIMARY KEY (worker_id, skill_id)
);

-- ── Worker Shifts ───────────────────────────────────────────────────────────
CREATE TABLE worker_shifts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id UUID NOT NULL REFERENCES workers(id),
    shift_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_holiday BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(worker_id, shift_date)
);

-- ── Worker Availability ─────────────────────────────────────────────────────
CREATE TABLE worker_availability (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    worker_id UUID NOT NULL REFERENCES workers(id),
    status worker_status NOT NULL,
    reason TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_worker_availability_active ON worker_availability(worker_id, status)
    WHERE ended_at IS NULL;

-- ── Vehicles ────────────────────────────────────────────────────────────────
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID NOT NULL REFERENCES departments(id),
    registration_number TEXT UNIQUE NOT NULL,
    vehicle_type TEXT NOT NULL,
    capacity JSONB DEFAULT '{}',
    status vehicle_status DEFAULT 'available',
    current_location GEOMETRY(Point, 4326),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- ── Equipment ───────────────────────────────────────────────────────────────
CREATE TABLE equipment (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    department_id UUID NOT NULL REFERENCES departments(id),
    name TEXT NOT NULL,
    equipment_type TEXT NOT NULL,
    quantity_total INTEGER NOT NULL DEFAULT 1,
    quantity_available INTEGER NOT NULL DEFAULT 1,
    status equipment_status DEFAULT 'available',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

-- =============================================================================
-- COMPLAINT & INCIDENT TABLES
-- =============================================================================

-- ── Locations ───────────────────────────────────────────────────────────────
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    coordinates GEOMETRY(Point, 4326) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    accuracy DOUBLE PRECISION,
    source location_source NOT NULL,
    address TEXT,
    landmark TEXT,
    ward_id UUID REFERENCES wards(id),
    municipality_id UUID REFERENCES municipalities(id),
    raw_input TEXT,
    geocoded_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_locations_geo ON locations USING GIST(coordinates);

-- ── Complaints ──────────────────────────────────────────────────────────────
CREATE TABLE complaints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_number TEXT UNIQUE NOT NULL,
    citizen_id UUID NOT NULL REFERENCES citizens(id),
    location_id UUID REFERENCES locations(id),
    status complaint_status DEFAULT 'submitted',
    -- Original citizen input
    original_text TEXT,
    original_language TEXT,
    original_voice_url TEXT,
    original_image_urls TEXT[],
    translated_text TEXT,
    -- AI classification results
    ai_category TEXT,
    ai_subcategory TEXT,
    ai_severity severity_level,
    ai_summary TEXT,
    ai_department_id UUID REFERENCES departments(id),
    ai_confidence DOUBLE PRECISION,
    ai_classification JSONB DEFAULT '{}',
    -- Verified / human-reviewed classification
    verified_category TEXT,
    verified_department_id UUID REFERENCES departments(id),
    -- Priority
    priority_score DOUBLE PRECISION,
    priority_level priority_level,
    priority_reasons TEXT[],
    -- Relationships
    master_incident_id UUID,
    municipality_id UUID REFERENCES municipalities(id),
    ward_id UUID REFERENCES wards(id),
    -- Timestamps
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    classified_at TIMESTAMPTZ,
    assigned_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_complaints_status ON complaints(status);
CREATE INDEX idx_complaints_citizen ON complaints(citizen_id);
CREATE INDEX idx_complaints_municipality ON complaints(municipality_id);
CREATE INDEX idx_complaints_priority ON complaints(priority_level);
CREATE INDEX idx_complaints_number ON complaints(complaint_number);

-- ── Complaint Messages ──────────────────────────────────────────────────────
CREATE TABLE complaint_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id UUID NOT NULL REFERENCES complaints(id),
    sender_id UUID NOT NULL REFERENCES user_profiles(id),
    message TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Complaint Evidence ──────────────────────────────────────────────────────
CREATE TABLE complaint_evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id UUID NOT NULL REFERENCES complaints(id),
    uploader_id UUID NOT NULL REFERENCES user_profiles(id),
    media_type media_type NOT NULL,
    storage_path TEXT NOT NULL,
    storage_url TEXT,
    file_name TEXT,
    file_size INTEGER,
    mime_type TEXT,
    stage evidence_stage DEFAULT 'before',
    location GEOMETRY(Point, 4326),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Master Incidents ────────────────────────────────────────────────────────
CREATE TABLE master_incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_number TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status incident_status DEFAULT 'open',
    category TEXT,
    subcategory TEXT,
    department_id UUID REFERENCES departments(id),
    location_id UUID REFERENCES locations(id),
    centroid GEOMETRY(Point, 4326),
    affected_radius DOUBLE PRECISION,
    -- Priority
    priority_score DOUBLE PRECISION,
    priority_level priority_level,
    priority_reasons TEXT[],
    -- Metrics
    complaint_count INTEGER DEFAULT 0,
    estimated_affected_population INTEGER,
    -- Classification
    severity severity_level,
    safety_risk BOOLEAN DEFAULT FALSE,
    critical_infrastructure BOOLEAN DEFAULT FALSE,
    near_vulnerable_location BOOLEAN DEFAULT FALSE,
    -- Municipality
    municipality_id UUID REFERENCES municipalities(id),
    ward_id UUID REFERENCES wards(id),
    -- SLA
    sla_policy_id UUID,
    sla_deadline TIMESTAMPTZ,
    sla_breached BOOLEAN DEFAULT FALSE,
    -- Timestamps
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    triaged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_incidents_status ON master_incidents(status);
CREATE INDEX idx_incidents_geo ON master_incidents USING GIST(centroid);
CREATE INDEX idx_incidents_priority ON master_incidents(priority_level);
CREATE INDEX idx_incidents_department ON master_incidents(department_id);

-- ── Incident-Complaint Link ─────────────────────────────────────────────────
CREATE TABLE incident_complaints (
    incident_id UUID NOT NULL REFERENCES master_incidents(id),
    complaint_id UUID NOT NULL REFERENCES complaints(id),
    similarity_score DOUBLE PRECISION,
    linked_by TEXT DEFAULT 'system',
    linked_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (incident_id, complaint_id)
);

-- Update foreign key on complaints
ALTER TABLE complaints
    ADD CONSTRAINT fk_complaints_incident
    FOREIGN KEY (master_incident_id) REFERENCES master_incidents(id);

-- ── Incident History ────────────────────────────────────────────────────────
CREATE TABLE incident_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES master_incidents(id),
    action TEXT NOT NULL,
    actor_id UUID REFERENCES user_profiles(id),
    old_value JSONB,
    new_value JSONB,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- SLA TABLES
-- =============================================================================

CREATE TABLE sla_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipality_id UUID NOT NULL REFERENCES municipalities(id),
    department_id UUID REFERENCES departments(id),
    category TEXT,
    priority_level priority_level,
    response_time_minutes INTEGER NOT NULL,
    resolution_time_minutes INTEGER NOT NULL,
    escalation_time_minutes INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE sla_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID REFERENCES master_incidents(id),
    complaint_id UUID REFERENCES complaints(id),
    sla_policy_id UUID NOT NULL REFERENCES sla_policies(id),
    event_type TEXT NOT NULL,
    deadline TIMESTAMPTZ NOT NULL,
    met_at TIMESTAMPTZ,
    breached BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- TASK & ASSIGNMENT TABLES
-- =============================================================================

-- ── Tasks ───────────────────────────────────────────────────────────────────
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_number TEXT UNIQUE NOT NULL,
    incident_id UUID NOT NULL REFERENCES master_incidents(id),
    title TEXT NOT NULL,
    description TEXT,
    status task_status DEFAULT 'pending',
    priority_level priority_level,
    -- Requirements
    required_skills UUID[],
    required_equipment UUID[],
    required_vehicle_type TEXT,
    required_worker_count INTEGER DEFAULT 1,
    -- Assignment
    assigned_team_id UUID REFERENCES teams(id),
    -- Timing
    estimated_duration_minutes INTEGER,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    -- SLA
    sla_deadline TIMESTAMPTZ,
    -- Location
    location_id UUID REFERENCES locations(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_incident ON tasks(incident_id);

-- ── Assignments ─────────────────────────────────────────────────────────────
CREATE TABLE assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID NOT NULL REFERENCES tasks(id),
    worker_id UUID NOT NULL REFERENCES workers(id),
    status assignment_status DEFAULT 'recommended',
    -- Matching scores
    skill_match_score DOUBLE PRECISION,
    distance_km DOUBLE PRECISION,
    workload_score DOUBLE PRECISION,
    overall_score DOUBLE PRECISION,
    -- AI reasoning
    recommendation_reasons TEXT[],
    -- Review
    reviewed_by UUID REFERENCES user_profiles(id),
    reviewed_at TIMESTAMPTZ,
    rejection_reason TEXT,
    -- Timing
    accepted_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assignments_worker ON assignments(worker_id);
CREATE INDEX idx_assignments_task ON assignments(task_id);
CREATE INDEX idx_assignments_status ON assignments(status);

-- ── Routes ──────────────────────────────────────────────────────────────────
CREATE TABLE routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id UUID REFERENCES assignments(id),
    worker_id UUID NOT NULL REFERENCES workers(id),
    origin GEOMETRY(Point, 4326),
    destination GEOMETRY(Point, 4326),
    distance_meters DOUBLE PRECISION,
    duration_seconds DOUBLE PRECISION,
    geometry GEOMETRY(LineString, 4326),
    waypoints JSONB DEFAULT '[]',
    provider TEXT DEFAULT 'osrm',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- RESOLUTION & VERIFICATION TABLES
-- =============================================================================

CREATE TABLE resolutions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    incident_id UUID NOT NULL REFERENCES master_incidents(id),
    task_id UUID REFERENCES tasks(id),
    resolver_id UUID NOT NULL REFERENCES user_profiles(id),
    description TEXT,
    resolution_type TEXT,
    -- AI verification
    ai_verification_score DOUBLE PRECISION,
    ai_verification_status TEXT,
    ai_verification_reasons TEXT[],
    -- Evidence
    before_evidence_ids UUID[],
    after_evidence_ids UUID[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE citizen_confirmations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    complaint_id UUID NOT NULL REFERENCES complaints(id),
    citizen_id UUID NOT NULL REFERENCES citizens(id),
    status confirmation_status NOT NULL,
    feedback TEXT,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- NOTIFICATIONS
-- =============================================================================

CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES user_profiles(id),
    channel notification_channel NOT NULL DEFAULT 'in_app',
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB DEFAULT '{}',
    status notification_status DEFAULT 'pending',
    event_type TEXT NOT NULL,
    reference_type TEXT,
    reference_id UUID,
    sent_at TIMESTAMPTZ,
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, status);

-- =============================================================================
-- PREDICTIONS
-- =============================================================================

CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipality_id UUID NOT NULL REFERENCES municipalities(id),
    prediction_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    confidence DOUBLE PRECISION,
    data JSONB DEFAULT '{}',
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    data_points_used INTEGER,
    model_version TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- AUDIT LOG
-- =============================================================================

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID REFERENCES user_profiles(id),
    actor_role user_role,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    old_value JSONB,
    new_value JSONB,
    reason TEXT,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_actor ON audit_logs(actor_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created ON audit_logs(created_at);

-- =============================================================================
-- BACKGROUND JOBS
-- =============================================================================

CREATE TABLE background_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type TEXT NOT NULL,
    status job_status DEFAULT 'queued',
    payload JSONB DEFAULT '{}',
    result JSONB,
    error TEXT,
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON background_jobs(status, scheduled_at);

-- =============================================================================
-- COMPLAINT NUMBER SEQUENCE
-- =============================================================================

CREATE SEQUENCE complaint_number_seq START 1;
CREATE SEQUENCE incident_number_seq START 1;
CREATE SEQUENCE task_number_seq START 1;

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Auto-generate complaint numbers
CREATE OR REPLACE FUNCTION generate_complaint_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.complaint_number := 'CMP-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('complaint_number_seq')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_complaint_number
    BEFORE INSERT ON complaints
    FOR EACH ROW
    WHEN (NEW.complaint_number IS NULL)
    EXECUTE FUNCTION generate_complaint_number();

-- Auto-generate incident numbers
CREATE OR REPLACE FUNCTION generate_incident_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.incident_number := 'INC-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('incident_number_seq')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_incident_number
    BEFORE INSERT ON master_incidents
    FOR EACH ROW
    WHEN (NEW.incident_number IS NULL)
    EXECUTE FUNCTION generate_incident_number();

-- Auto-generate task numbers
CREATE OR REPLACE FUNCTION generate_task_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.task_number := 'TSK-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('task_number_seq')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_task_number
    BEFORE INSERT ON tasks
    FOR EACH ROW
    WHEN (NEW.task_number IS NULL)
    EXECUTE FUNCTION generate_task_number();

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER trg_municipalities_updated BEFORE UPDATE ON municipalities FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_wards_updated BEFORE UPDATE ON wards FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_departments_updated BEFORE UPDATE ON departments FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_user_profiles_updated BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_citizens_updated BEFORE UPDATE ON citizens FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_teams_updated BEFORE UPDATE ON teams FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_workers_updated BEFORE UPDATE ON workers FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_complaints_updated BEFORE UPDATE ON complaints FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_incidents_updated BEFORE UPDATE ON master_incidents FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_tasks_updated BEFORE UPDATE ON tasks FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_assignments_updated BEFORE UPDATE ON assignments FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_vehicles_updated BEFORE UPDATE ON vehicles FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_equipment_updated BEFORE UPDATE ON equipment FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_sla_policies_updated BEFORE UPDATE ON sla_policies FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- ROW LEVEL SECURITY
-- =============================================================================

-- Enable RLS on all tables
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE citizens ENABLE ROW LEVEL SECURITY;
ALTER TABLE workers ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaint_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE complaint_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- User profiles: users can read their own, admins can read all
CREATE POLICY "users_read_own" ON user_profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "admins_read_all_profiles" ON user_profiles
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid()
            AND role IN ('municipal_admin', 'system_admin', 'supervisor', 'department_officer')
        )
    );

CREATE POLICY "users_update_own" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- Complaints: citizens see own, officials see department/all
CREATE POLICY "citizens_read_own_complaints" ON complaints
    FOR SELECT USING (
        citizen_id IN (SELECT id FROM citizens WHERE user_id = auth.uid())
    );

CREATE POLICY "officials_read_complaints" ON complaints
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE id = auth.uid()
            AND role IN ('worker', 'supervisor', 'department_officer', 'municipal_admin', 'system_admin')
        )
    );

-- Notifications: users see their own only
CREATE POLICY "users_read_own_notifications" ON notifications
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "users_update_own_notifications" ON notifications
    FOR UPDATE USING (user_id = auth.uid());

-- Service role bypasses all RLS (used by backend)
-- This is automatic when using the service_role key
