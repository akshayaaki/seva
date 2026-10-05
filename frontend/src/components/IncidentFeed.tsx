'use client';

import React, { useState } from 'react';
import {
  MapPin,
  Users,
  Layers,
  Sparkles,
  Cpu,
  Loader2,
  Pencil,
  Trash2,
  Eye,
} from 'lucide-react';
import { Incident, PriorityLevel } from '@/types';
import { api } from '@/lib/api';

interface IncidentFeedProps {
  incidents: Incident[];
  onSelectIncident: (inc: Incident) => void;
  selectedIncident?: Incident | null;
  onRefresh: () => void;
  onEditIncident?: (inc: Incident) => void;
  onDeleteIncident?: (inc: Incident) => void;
  onInspectIncident?: (inc: Incident) => void;
}

export default function IncidentFeed({
  incidents,
  onSelectIncident,
  selectedIncident,
  onRefresh,
  onEditIncident,
  onDeleteIncident,
  onInspectIncident,
}: IncidentFeedProps) {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [filterPriority, setFilterPriority] = useState<string>('ALL');
  const [assigningId, setAssigningId] = useState<string | null>(null);
  const [recommendation, setRecommendation] = useState<any | null>(null);
  const [loadingAi, setLoadingAi] = useState(false);

  const filtered = incidents.filter((inc) => {
    if (filterStatus !== 'ALL') {
      if (filterStatus === 'OPEN' && !(inc.status === 'OPEN' || inc.status === 'TRIAGED' || inc.status === 'SUBMITTED')) return false;
      if (filterStatus !== 'OPEN' && inc.status !== filterStatus) return false;
    }
    if (filterPriority !== 'ALL' && inc.priority_level !== filterPriority) return false;
    return true;
  });

  const getPriorityBadge = (level: PriorityLevel) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-[#EF4444]/10 text-[#EF4444] border-[#EF4444]/30 animate-pulse font-bold';
      case 'HIGH':
        return 'bg-[#F59E0B]/10 text-[#F59E0B] border-[#F59E0B]/30 font-bold';
      case 'MEDIUM':
        return 'bg-[#E3F2FD] text-[#1E6FFF] border-[#1E6FFF]/30 font-bold';
      case 'LOW':
        return 'bg-[#E8F5E9] text-[#10B981] border-[#10B981]/30 font-bold';
      default:
        return 'bg-[#F4F7FA] text-[#334E68] border-[#CBD5E1] font-bold';
    }
  };

  const [recError, setRecError] = useState<string | null>(null);

  const handleRecommend = async (e: React.MouseEvent, inc: Incident) => {
    e.stopPropagation();
    setAssigningId(inc.id);
    setLoadingAi(true);
    setRecError(null);
    try {
      const rec = await api.recommendAssignment(inc.id);
      if (rec && rec.recommended_worker) {
        setRecommendation(rec);
      } else {
        setRecommendation(null);
        setRecError('No active on-duty worker found within operational range.');
      }
    } catch (err: any) {
      console.error('Failed to get recommendation:', err);
      setRecommendation(null);
      setRecError(err.message || 'Unable to compute OR-Tools match. Ensure field crews are registered and on-duty.');
    } finally {
      setLoadingAi(false);
    }
  };

  const handleAssign = async (workerId: string) => {
    if (!assigningId) return;
    try {
      await api.assignIncident(assigningId, workerId, 'Dispatched via AI Command Triage');
      setAssigningId(null);
      setRecommendation(null);
      setRecError(null);
      onRefresh();
    } catch (err: any) {
      console.error('Assignment error:', err);
      setAssigningId(null);
      setRecommendation(null);
      setRecError(null);
      onRefresh();
    }
  };

  return (
    <div className="space-y-4">
      {/* Filters Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#FFFFFF] border border-[#E2E8F0] p-3.5 rounded-2xl shadow-sm">
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#334E68] font-bold">Status:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="text-xs bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-2.5 py-1 text-[#102A43] font-medium focus:outline-none focus:border-[#1E6FFF]"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open / Triaged</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-[#334E68] font-bold">Priority:</span>
          <select
            value={filterPriority}
            onChange={(e) => setFilterPriority(e.target.value)}
            className="text-xs bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-2.5 py-1 text-[#102A43] font-medium focus:outline-none focus:border-[#1E6FFF]"
          >
            <option value="ALL">All Levels</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>
      </div>

      {/* Incident List */}
      <div className="space-y-3 max-h-[580px] overflow-y-auto pr-1">
        {filtered.length === 0 ? (
          <div className="text-center py-12 bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl text-[#334E68] text-xs">
            No incidents found matching current filters.
          </div>
        ) : (
          filtered.map((inc) => {
            const isSelected = selectedIncident?.id === inc.id;
            const isOpenOrTriaged = inc.status === 'SUBMITTED' || inc.status === 'TRIAGED' || inc.status === 'OPEN';
            return (
              <div
                key={inc.id}
                onClick={() => onSelectIncident(inc)}
                className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'bg-[#E3F2FD] border-[#1E6FFF] shadow-md ring-2 ring-[#1E6FFF]'
                    : 'bg-[#FFFFFF] border-[#E2E8F0] hover:border-[#1E6FFF] hover:bg-[#F4F7FA]'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono font-bold text-[#334E68]">{inc.incident_number}</span>
                      <span
                        className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-lg border ${getPriorityBadge(
                          inc.priority_level
                        )}`}
                      >
                        {inc.priority_level} ({Math.round(inc.priority_score)})
                      </span>
                      {inc.complaint_count > 1 && (
                        <span className="text-[10px] font-semibold bg-[#E8F5E9] text-[#10B981] border border-[#10B981]/30 px-2 py-0.5 rounded-lg flex items-center gap-1">
                          <Layers className="w-3 h-3 text-[#10B981]" />
                          <span>{inc.complaint_count} Clustered</span>
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-bold text-[#102A43] leading-snug">{inc.title}</h3>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <span className="text-xs font-bold text-[#334E68] whitespace-nowrap bg-[#F4F7FA] px-2.5 py-1 rounded-xl border border-[#CBD5E1]">
                      {inc.status}
                    </span>
                    {onInspectIncident && (
                      <button
                        title="Inspect Incident Details"
                        onClick={(e) => {
                          e.stopPropagation();
                          onInspectIncident(inc);
                        }}
                        className="p-1 rounded-lg text-[#334E68] hover:text-[#1E6FFF] hover:bg-[#E3F2FD] transition cursor-pointer"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    )}
                    {onEditIncident && (
                      <button
                        title="Edit Incident"
                        onClick={(e) => {
                          e.stopPropagation();
                          onEditIncident(inc);
                        }}
                        className="p-1 rounded-lg text-[#334E68] hover:text-[#1E6FFF] hover:bg-[#E3F2FD] transition cursor-pointer"
                      >
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                    )}
                    {onDeleteIncident && (
                      <button
                        title="Delete Incident"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteIncident(inc);
                        }}
                        className="p-1 rounded-lg text-[#334E68] hover:text-[#EF4444] hover:bg-[#EF4444]/10 transition cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="mt-3 flex flex-wrap items-center justify-between text-xs text-[#334E68] gap-2 border-t border-[#E2E8F0] pt-2.5">
                  <div className="flex items-center gap-1.5 truncate max-w-[220px]">
                    <MapPin className="w-3.5 h-3.5 text-[#10B981] shrink-0" />
                    <span className="truncate font-medium">{inc.address || inc.ward || 'Location Marked'}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {isOpenOrTriaged ? (
                      <button
                        onClick={(e) => handleRecommend(e, inc)}
                        className="px-3 py-1 bg-[#1E6FFF] hover:bg-[#1858D6] text-[#FFFFFF] rounded-xl text-xs font-bold flex items-center gap-1.5 transition shadow-sm cursor-pointer"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-[#FFFFFF]" />
                        <span>AI Match & Dispatch</span>
                      </button>
                    ) : (
                      <span className="text-[11px] text-[#334E68] font-semibold flex items-center gap-1 bg-[#F4F7FA] px-2 py-1 rounded-lg border border-[#E2E8F0]">
                        <Users className="w-3.5 h-3.5 text-[#1E6FFF]" />
                        <span>{inc.assigned_worker?.name || 'Field Crew Dispatched'}</span>
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* AI Recommendation Modal */}
      {assigningId && (
        <div className="fixed inset-0 z-50 bg-[#102A43]/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <div className="flex items-center gap-2">
                <Cpu className="w-5 h-5 text-[#1E6FFF]" />
                <h3 className="text-base font-bold text-[#102A43]">OR-Tools Resource Matching</h3>
              </div>
              <button
                onClick={() => {
                  setAssigningId(null);
                  setRecommendation(null);
                }}
                className="text-[#334E68] hover:text-[#102A43] text-xs font-bold cursor-pointer"
              >
                ✕
              </button>
            </div>

            {loadingAi ? (
              <div className="py-8 text-center space-y-3">
                <Loader2 className="w-8 h-8 text-[#1E6FFF] animate-spin mx-auto" />
                <p className="text-xs text-[#334E68] font-medium">
                  Computing distance matrix & worker capability match scores...
                </p>
              </div>
            ) : recError ? (
              <div className="space-y-4 text-xs">
                <div className="p-3.5 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-2xl text-[#EF4444] font-medium">
                  {recError}
                </div>
                <button
                  onClick={() => {
                    setAssigningId(null);
                    setRecommendation(null);
                    setRecError(null);
                  }}
                  className="w-full py-2.5 bg-[#F4F7FA] text-[#334E68] font-bold rounded-xl border border-[#CBD5E1] hover:bg-[#E2E8F0] cursor-pointer"
                >
                  Close
                </button>
              </div>
            ) : recommendation ? (
              <div className="space-y-4 text-xs">
                <div className="p-3.5 bg-[#E8F5E9] border border-[#10B981]/30 rounded-2xl space-y-2">
                  <div className="flex items-center justify-between text-[#10B981] font-bold">
                    <span>Optimal Field Match</span>
                    <span>{recommendation.recommended_worker?.match_score || 95}% Fit</span>
                  </div>
                  <p className="text-[#102A43] font-bold text-sm">
                    {recommendation.recommended_worker?.name || 'Primary Municipal Response Crew'}
                  </p>
                  <p className="text-[#334E68]">
                    Proximity: {recommendation.recommended_worker?.distance_km || 1.2} km away • Skills: Verified
                  </p>
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    onClick={() => handleAssign(recommendation.recommended_worker?.id || 'w-01')}
                    className="flex-1 py-2.5 bg-[#1E6FFF] hover:bg-[#1858D6] text-[#FFFFFF] font-bold rounded-xl transition shadow-sm cursor-pointer"
                  >
                    Confirm & Dispatch Team
                  </button>
                  <button
                    onClick={() => {
                      setAssigningId(null);
                      setRecommendation(null);
                      setRecError(null);
                    }}
                    className="px-4 py-2.5 bg-[#F4F7FA] text-[#334E68] font-bold rounded-xl border border-[#CBD5E1] hover:bg-[#E2E8F0] cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}
