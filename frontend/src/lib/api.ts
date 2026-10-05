/**
 * Janseva AI — Frontend API Client
 * Seamlessly interfaces with FastAPI backend services.
 */
import { Complaint, Incident, WorkerTask, AdminAnalytics } from '@/types';

const getBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    // In browser, use relative URL so Next.js proxies to backend without CORS or port mismatch
    if (process.env.NEXT_PUBLIC_BACKEND_URL && !process.env.NEXT_PUBLIC_BACKEND_URL.includes('localhost')) {
      return process.env.NEXT_PUBLIC_BACKEND_URL;
    }
    return '';
  }
  // On server (SSR)
  return process.env.BACKEND_INTERNAL_URL || process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000';
};

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const path = endpoint.startsWith('/api') ? endpoint : `/api${endpoint}`;
    const baseUrl = getBaseUrl();
    const url = `${baseUrl}${path}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Request failed with status ${response.status}`);
      }

      return await response.json();
    } catch (error: any) {
      // In browser, if relative proxy threw a network error, attempt direct connection to 127.0.0.1:8000
      if (typeof window !== 'undefined' && !url.startsWith('http://127.0.0.1:8000')) {
        try {
          const directUrl = `http://127.0.0.1:8000${path}`;
          const directResp = await fetch(directUrl, { ...options, headers });
          if (directResp.ok) {
            return await directResp.json();
          }
        } catch {
          // Direct fallback failed too
        }
      }
      throw error;
    }
  }

  // --- Citizen Complaints ---
  async translateGrievance(text: string): Promise<{
    original_text: string;
    translated_text: string;
    detected_language: string;
    language_name?: string;
  }> {
    const LANG_MAP: Record<string, string> = {
      hi: 'Hindi',
      mr: 'Marathi',
      gu: 'Gujarati',
      ta: 'Tamil',
      te: 'Telugu',
      kn: 'Kannada',
      bn: 'Bengali',
      pa: 'Punjabi',
      ml: 'Malayalam',
      ur: 'Urdu',
      or: 'Odia',
      en: 'English',
    };

    // 1. Try Backend API
    try {
      const res: any = await this.request('/complaints/translate', {
        method: 'POST',
        body: JSON.stringify({ text, target_lang: 'en' }),
      });
      if (res && res.translated_text && res.translated_text !== text) {
        return res;
      }
    } catch {
      // Fallback to client-side translation
    }

    // 2. Direct browser-side neural translation fallback
    try {
      const encoded = encodeURIComponent(text.trim());
      const gtxUrl = `https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q=${encoded}`;
      const resp = await fetch(gtxUrl);
      if (resp.ok) {
        const data = await resp.json();
        const translated = (data[0] || [])
          .map((item: any) => item[0])
          .filter(Boolean)
          .join('');
        const detected = String(data[2] || 'en').toLowerCase();
        return {
          original_text: text,
          translated_text: translated || text,
          detected_language: detected,
          language_name: LANG_MAP[detected] || detected.toUpperCase(),
        };
      }
    } catch {
      // Direct fetch fallback failed
    }

    return {
      original_text: text,
      translated_text: text,
      detected_language: 'en',
      language_name: 'Original',
    };
  }
  async submitComplaint(data: {
    description: string;
    latitude: number;
    longitude: number;
    citizen_name?: string;
    citizen_phone?: string;
    address?: string;
    ward?: string;
    media_urls?: string[];
  }): Promise<Complaint> {
    const payload = {
      text: data.description,
      description: data.description,
      citizen_name: data.citizen_name,
      citizen_phone: data.citizen_phone,
      image_urls: data.media_urls || [],
      media_urls: data.media_urls || [],
      latitude: data.latitude,
      longitude: data.longitude,
      address: data.address,
      ward: data.ward,
      location: {
        latitude: data.latitude,
        longitude: data.longitude,
        address: data.address,
        landmark: data.ward,
      },
    };

    const res: any = await this.request<any>('/complaints', {
      method: 'POST',
      body: JSON.stringify(payload),
    });

    return {
      id: res.id || ('comp-' + Math.random().toString(36).substring(7)),
      tracking_id: res.tracking_id || res.complaint_number || ('JAN-' + (res.id ? res.id.slice(0, 8).toUpperCase() : '2026-001')),
      category: res.category || res.ai_category || 'Civic Grievance',
      description: res.original_text || data.description,
      latitude: res.location?.latitude || data.latitude,
      longitude: res.location?.longitude || data.longitude,
      address: res.location?.address || data.address || 'Reported Location',
      ward: data.ward || 'Ward 12',
      status: 'SUBMITTED',
      created_at: res.created_at || new Date().toISOString(),
      updated_at: res.created_at || new Date().toISOString(),
    };
  }

  async getComplaint(trackingId: string): Promise<Complaint> {
    return this.request<Complaint>(`/complaints/${encodeURIComponent(trackingId)}`);
  }

  async confirmResolution(trackingId: string, rating?: number, feedback?: string): Promise<any> {
    return this.request(`/complaints/${encodeURIComponent(trackingId)}/confirm`, {
      method: 'POST',
      body: JSON.stringify({ rating, feedback }),
    });
  }

  async reopenComplaint(trackingId: string, reason: string): Promise<any> {
    return this.request(`/complaints/${encodeURIComponent(trackingId)}/reopen`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  }

  // --- Incidents & Triage ---
  async getIncidents(params: {
    status?: string;
    priority?: string;
    ward?: string;
    limit?: number;
  } = {}): Promise<Incident[]> {
    const query = new URLSearchParams();
    if (params.status) query.set('status', params.status);
    if (params.priority) query.set('priority', params.priority);
    if (params.ward) query.set('ward', params.ward);
    if (params.limit) query.set('page_size', params.limit.toString());

    const res: any = await this.request<any>(`/incidents?${query.toString()}`);
    const items: any[] = Array.isArray(res) ? res : (res?.incidents || []);

    return items.map((inc: any) => ({
      id: inc.id,
      incident_number: inc.incident_number,
      municipality_id: inc.municipality_id || 'muni-01',
      department_id: inc.department_id,
      category: inc.category || 'Civic Infrastructure',
      title: inc.title || 'Civic Incident',
      summary: inc.description || inc.title,
      latitude: inc.location?.latitude || 19.0760,
      longitude: inc.location?.longitude || 72.8777,
      address: inc.location?.address || inc.location?.geocoded_address || 'Mumbai Municipal Area',
      ward: inc.ward_id || 'Ward 12',
      priority_score: inc.priority_score || 50,
      priority_level: (inc.priority_level?.toUpperCase() || 'MEDIUM') as any,
      status: (inc.status?.toUpperCase() || 'TRIAGED') as any,
      complaint_count: inc.complaint_count || 1,
      created_at: inc.created_at || new Date().toISOString(),
      updated_at: inc.created_at || new Date().toISOString(),
    }));
  }

  async getIncident(id: string): Promise<Incident> {
    const inc: any = await this.request<any>(`/incidents/${id}`);
    return {
      id: inc.id,
      incident_number: inc.incident_number,
      municipality_id: inc.municipality_id || 'muni-01',
      department_id: inc.department_id,
      category: inc.category || 'Civic Infrastructure',
      title: inc.title || 'Civic Incident',
      summary: inc.description || inc.title,
      latitude: inc.location?.latitude || 19.0760,
      longitude: inc.location?.longitude || 72.8777,
      address: inc.location?.address || inc.location?.geocoded_address || 'Mumbai Municipal Area',
      ward: inc.ward_id || 'Ward 12',
      priority_score: inc.priority_score || 50,
      priority_level: (inc.priority_level?.toUpperCase() || 'MEDIUM') as any,
      status: (inc.status?.toUpperCase() || 'OPEN') as any,
      complaint_count: inc.complaint_count || 1,
      created_at: inc.created_at || new Date().toISOString(),
      updated_at: inc.created_at || new Date().toISOString(),
    };
  }

  async createIncident(data: {
    title: string;
    description?: string;
    category?: string;
    department_id?: string;
    priority_level?: string;
    priority_score?: number;
    status?: string;
    latitude?: number;
    longitude?: number;
    address?: string;
    ward_id?: string;
  }): Promise<Incident> {
    const res: any = await this.request('/incidents', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return {
      id: res.id,
      incident_number: res.incident_number,
      municipality_id: res.municipality_id || 'muni-01',
      department_id: res.department_id,
      category: res.category || data.category || 'Civic Infrastructure',
      title: res.title || data.title,
      summary: res.description || data.description,
      latitude: res.location?.latitude || data.latitude || 19.0760,
      longitude: res.location?.longitude || data.longitude || 72.8777,
      address: res.location?.address || data.address || 'Reported Incident Area',
      ward: data.ward_id || 'Ward 12',
      priority_score: res.priority_score || data.priority_score || 50,
      priority_level: (res.priority_level?.toUpperCase() || data.priority_level?.toUpperCase() || 'MEDIUM') as any,
      status: (res.status?.toUpperCase() || 'OPEN') as any,
      complaint_count: 1,
      created_at: res.created_at || new Date().toISOString(),
      updated_at: res.created_at || new Date().toISOString(),
    };
  }

  async updateIncident(id: string, data: {
    title?: string;
    description?: string;
    category?: string;
    department_id?: string;
    priority_level?: string;
    priority_score?: number;
    status?: string;
    ward_id?: string;
  }): Promise<any> {
    return this.request(`/incidents/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteIncident(id: string): Promise<any> {
    return this.request(`/incidents/${id}`, {
      method: 'DELETE',
    });
  }

  async recommendAssignment(incidentId: string): Promise<any> {
    return this.request(`/incidents/${incidentId}/recommend-assignment`, {
      method: 'POST',
    });
  }

  async assignIncident(incidentId: string, workerId: string, notes?: string): Promise<any> {
    return this.request(`/incidents/${incidentId}/assign`, {
      method: 'POST',
      body: JSON.stringify({ worker_id: workerId, notes }),
    });
  }

  // --- Field Worker Tasks ---
  async getWorkerTasks(workerId?: string): Promise<WorkerTask[]> {
    const query = workerId ? `?worker_id=${workerId}` : '';
    const res: any = await this.request<any>(`/incidents/tasks/my-tasks${query}`);
    const items: any[] = Array.isArray(res) ? res : [];

    return items.map((t: any) => ({
      id: t.id,
      task_number: t.task_number || `TSK-${t.id.slice(0, 8)}`,
      incident_id: t.incident_id,
      worker_id: workerId || 'w-101',
      title: t.title,
      description: t.description,
      priority_level: (t.priority_level?.toUpperCase() || 'MEDIUM') as any,
      status: (t.status?.toUpperCase() || 'PENDING') as any,
      latitude: t.location?.latitude || 19.0760,
      longitude: t.location?.longitude || 72.8777,
      address: t.location?.address || 'Mumbai Central Ward',
      assigned_at: t.created_at || new Date().toISOString(),
      started_at: t.started_at,
      completed_at: t.completed_at,
    }));
  }

  async updateTaskStatus(taskId: string, status: string, payload: {
    notes?: string;
    evidence_url?: string;
    latitude?: number;
    longitude?: number;
  }): Promise<any> {
    return this.request(`/incidents/tasks/${taskId}/status`, {
      method: 'POST',
      body: JSON.stringify({ status, ...payload }),
    });
  }

  // --- Admin & Analytics ---
  async getAdminDashboard(): Promise<AdminAnalytics> {
    return this.request<AdminAnalytics>('/admin/dashboard');
  }

  async getDepartments(): Promise<any[]> {
    return this.request<any[]>('/admin/departments');
  }

  async getWorkers(): Promise<any[]> {
    return this.request<any[]>('/admin/workers');
  }

  async getAuditLogs(limit: number = 50): Promise<any[]> {
    return this.request<any[]>(`/admin/audit-logs?limit=${limit}`);
  }
}

export const api = new ApiClient();
