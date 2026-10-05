'use client';

import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Building,
  Shield,
  FileSpreadsheet,
  Activity,
} from 'lucide-react';
import { AdminAnalytics } from '@/types';
import { api } from '@/lib/api';

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'analytics' | 'audit'>('analytics');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await api.getAdminDashboard();
        setAnalytics(data);

        const logs = await api.getAuditLogs(30);
        setAuditLogs(logs || []);
      } catch (err) {
        console.error('Failed to fetch admin dashboard:', err);
        setAnalytics({
          total_complaints: 0,
          active_incidents: 0,
          resolved_today: 0,
          sla_breach_rate: 0,
          avg_resolution_hours: 0,
          category_breakdown: {},
          ward_metrics: [],
          recent_activity: [],
        });
        setAuditLogs([]);
      }
    };

    fetchData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-[#FFFFFF] border border-[#E2E8F0] p-4 rounded-3xl space-y-1 shadow-sm">
          <span className="text-xs text-[#334E68] font-semibold flex items-center gap-1.5">
            <FileSpreadsheet className="w-3.5 h-3.5 text-[#1E6FFF]" /> Total Complaints
          </span>
          <p className="text-2xl font-black text-[#102A43]">{analytics?.total_complaints || 0}</p>
          <span className="text-[10px] text-[#10B981] font-bold">Live DB Count</span>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E2E8F0] p-4 rounded-3xl space-y-1 shadow-sm">
          <span className="text-xs text-[#334E68] font-semibold flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-[#1E6FFF]" /> Active Incidents
          </span>
          <p className="text-2xl font-black text-[#1E6FFF]">{analytics?.active_incidents || 0}</p>
          <span className="text-[10px] text-[#334E68]">Currently in field triage</span>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E2E8F0] p-4 rounded-3xl space-y-1 shadow-sm">
          <span className="text-xs text-[#334E68] font-semibold flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#10B981]" /> Resolved Today
          </span>
          <p className="text-2xl font-black text-[#10B981]">{analytics?.resolved_today || 0}</p>
          <span className="text-[10px] text-[#10B981] font-bold">Field work validated</span>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E2E8F0] p-4 rounded-3xl space-y-1 shadow-sm">
          <span className="text-xs text-[#334E68] font-semibold flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-[#1E6FFF]" /> Avg SLA Time
          </span>
          <p className="text-2xl font-black text-[#102A43]">{analytics?.avg_resolution_hours || 0}h</p>
          <span className="text-[10px] text-[#10B981] font-bold">Computed from resolution logs</span>
        </div>

        <div className="bg-[#FFFFFF] border border-[#E2E8F0] p-4 rounded-3xl space-y-1 shadow-sm">
          <span className="text-xs text-[#334E68] font-semibold flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-[#EF4444]" /> SLA Breach %
          </span>
          <p className="text-2xl font-black text-[#EF4444]">{analytics?.sla_breach_rate || 0}%</p>
          <span className="text-[10px] text-[#334E68]">Target &lt; 5%</span>
        </div>
      </div>

      {/* View Toggle */}
      <div className="flex gap-2 border-b border-[#E2E8F0] pb-3">
        <button
          onClick={() => setActiveTab('analytics')}
          className={`px-4 py-2 rounded-2xl text-xs font-bold transition shadow-sm cursor-pointer ${
            activeTab === 'analytics'
              ? 'bg-[#1E6FFF] text-[#FFFFFF]'
              : 'text-[#334E68] hover:text-[#102A43] bg-[#E3F2FD]/50'
          }`}
        >
          Municipal Analytics & Ward Heatmaps
        </button>
        <button
          onClick={() => setActiveTab('audit')}
          className={`px-4 py-2 rounded-2xl text-xs font-bold transition shadow-sm cursor-pointer ${
            activeTab === 'audit'
              ? 'bg-[#1E6FFF] text-[#FFFFFF]'
              : 'text-[#334E68] hover:text-[#102A43] bg-[#E3F2FD]/50'
          }`}
        >
          Immutable Audit Log (Security & Verification)
        </button>
      </div>

      {activeTab === 'analytics' ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Ward Breakdown Table */}
          <div className="lg:col-span-7 bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 space-y-4 shadow-sm">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-bold text-[#102A43] flex items-center gap-2">
                <Building className="w-4 h-4 text-[#1E6FFF]" />
                Ward-Level Resolution Metrics
              </h3>
              <span className="text-xs text-[#334E68]">All Municipal Wards</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-[#E2E8F0] text-[#334E68] text-[11px] uppercase tracking-wider">
                    <th className="py-2.5">Ward</th>
                    <th className="py-2.5">Total</th>
                    <th className="py-2.5">Resolved</th>
                    <th className="py-2.5">Pending</th>
                    <th className="py-2.5 text-right">Efficiency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#E2E8F0]">
                  {analytics && analytics.ward_metrics && analytics.ward_metrics.length > 0 ? (
                    analytics.ward_metrics.map((w) => {
                      const pct = w.total > 0 ? Math.round((w.resolved / w.total) * 100) : 0;
                      return (
                        <tr key={w.ward} className="hover:bg-[#F4F7FA]">
                          <td className="py-3 font-bold text-[#102A43]">{w.ward}</td>
                          <td className="py-3 text-[#334E68] font-semibold">{w.total}</td>
                          <td className="py-3 text-[#10B981] font-bold">{w.resolved}</td>
                          <td className="py-3 text-[#F59E0B] font-bold">{w.pending}</td>
                          <td className="py-3 text-right">
                            <span className="px-2.5 py-1 rounded-xl bg-[#E8F5E9] text-[#10B981] font-bold border border-[#10B981]/30">
                              {pct}%
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} className="py-8 text-center text-[#334E68] text-xs">
                        No ward resolution metrics recorded yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="lg:col-span-5 bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 space-y-4 shadow-sm">
            <h3 className="text-sm font-bold text-[#102A43] flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[#1E6FFF]" />
              Category Grievance Volume
            </h3>

            <div className="space-y-3">
              {analytics && Object.keys(analytics.category_breakdown || {}).length > 0 ? (
                Object.entries(analytics.category_breakdown).map(([cat, count]) => {
                  const maxVal = Math.max(...Object.values(analytics.category_breakdown), 1);
                  const percentage = Math.round((count / maxVal) * 100);
                  return (
                    <div key={cat} className="space-y-1">
                      <div className="flex justify-between text-xs text-[#334E68] font-semibold">
                        <span>{cat}</span>
                        <span className="font-bold text-[#102A43]">{count}</span>
                      </div>
                      <div className="w-full bg-[#F4F7FA] rounded-full h-2.5 overflow-hidden border border-[#CBD5E1]">
                        <div
                          className="bg-[#1E6FFF] h-full rounded-full transition-all duration-500"
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="py-8 text-center text-[#334E68] text-xs">
                  No category grievance data recorded yet.
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        /* Audit Log Table */
        <div className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 space-y-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-[#102A43] flex items-center gap-2">
                <Shield className="w-4 h-4 text-[#10B981]" />
                Municipal Action Audit Trail
              </h3>
              <p className="text-xs text-[#334E68] mt-0.5">
                Every grievance creation, AI score, assignment, and completion is recorded with IP and timestamp.
              </p>
            </div>
            <span className="text-xs bg-[#E8F5E9] px-3 py-1 rounded-xl text-[#10B981] font-mono font-bold border border-[#10B981]/30">
              Immutable
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E2E8F0] text-[#334E68] text-[11px] uppercase tracking-wider">
                  <th className="py-2.5">Timestamp</th>
                  <th className="py-2.5">Action</th>
                  <th className="py-2.5">Entity</th>
                  <th className="py-2.5">Operator</th>
                  <th className="py-2.5">Origin IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E2E8F0] font-mono text-[11px]">
                {auditLogs && auditLogs.length > 0 ? (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="hover:bg-[#F4F7FA]">
                      <td className="py-3 text-[#334E68]">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </td>
                      <td className="py-3 font-bold text-[#102A43]">{log.action}</td>
                      <td className="py-3 text-[#334E68]">
                        {log.entity_type} ({log.entity_id})
                      </td>
                      <td className="py-3 text-[#102A43] font-semibold">{log.performed_by}</td>
                      <td className="py-3 text-[#94A3B8]">{log.ip_address}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-[#334E68] text-xs font-sans">
                      No audit trail records found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
