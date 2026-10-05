export type PriorityLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';

export type IncidentStatus = 
  | 'OPEN'
  | 'SUBMITTED'
  | 'TRIAGED'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'RESOLVED'
  | 'CLOSED'
  | 'REOPENED';

export type TaskStatus =
  | 'PENDING'
  | 'ACCEPTED'
  | 'EN_ROUTE'
  | 'ON_SCENE'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'CANCELLED';

export interface Complaint {
  id: string;
  tracking_id: string;
  municipality_id?: string;
  citizen_name?: string;
  citizen_phone?: string;
  category: string;
  sub_category?: string;
  description: string;
  detected_language?: string;
  translated_description?: string;
  latitude: number;
  longitude: number;
  address?: string;
  ward?: string;
  landmark?: string;
  media_urls?: string[];
  severity?: string;
  status: IncidentStatus;
  incident_id?: string;
  created_at: string;
  updated_at: string;
  verification_status?: 'PENDING' | 'CONFIRMED' | 'REOPENED';
}

export interface Incident {
  id: string;
  incident_number: string;
  municipality_id: string;
  department_id?: string;
  category: string;
  title: string;
  summary?: string;
  latitude: number;
  longitude: number;
  address?: string;
  ward?: string;
  priority_score: number;
  priority_level: PriorityLevel;
  status: IncidentStatus;
  complaint_count: number;
  assigned_worker_id?: string;
  assigned_team_id?: string;
  sla_due_at?: string;
  sla_breached?: boolean;
  created_at: string;
  updated_at: string;
  assigned_worker?: {
    id: string;
    name: string;
    phone: string;
    role: string;
  };
}

export interface WorkerTask {
  id: string;
  task_number: string;
  incident_id: string;
  worker_id: string;
  title: string;
  description?: string;
  priority_level: PriorityLevel;
  status: TaskStatus;
  latitude: number;
  longitude: number;
  address?: string;
  before_photo_url?: string;
  after_photo_url?: string;
  resolution_notes?: string;
  assigned_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface AdminAnalytics {
  total_complaints: number;
  active_incidents: number;
  resolved_today: number;
  sla_breach_rate: number;
  avg_resolution_hours: number;
  category_breakdown: Record<string, number>;
  ward_metrics: Array<{
    ward: string;
    total: number;
    resolved: number;
    pending: number;
  }>;
  recent_activity: Array<{
    id: string;
    action: string;
    entity: string;
    timestamp: string;
    details?: string;
  }>;
}
