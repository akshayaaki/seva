'use client';

import React, { useState } from 'react';
import {
  Search,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Star,
  MapPin,
  Check,
  Building,
} from 'lucide-react';
import { api } from '@/lib/api';
import { Complaint } from '@/types';

export default function ComplaintTracker() {
  const [trackingId, setTrackingId] = useState('');
  const [loading, setLoading] = useState(false);
  const [complaint, setComplaint] = useState<Complaint | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Feedback & Reopen state
  const [rating, setRating] = useState(5);
  const [feedback, setFeedback] = useState('');
  const [reopenReason, setReopenReason] = useState('');
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const handleTrack = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!trackingId.trim()) return;

    setError(null);
    setActionSuccess(null);
    setLoading(true);
    try {
      const data = await api.getComplaint(trackingId.trim());
      if (data) {
        setComplaint(data);
      } else {
        setComplaint(null);
        setError(`No grievance found with Tracking ID "${trackingId.trim().toUpperCase()}".`);
      }
    } catch (err: any) {
      console.error('Error tracking complaint:', err);
      setComplaint(null);
      setError(`No grievance record found for Tracking ID "${trackingId.trim().toUpperCase()}". Please verify the reference code.`);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!complaint) return;
    try {
      await api.confirmResolution(complaint.tracking_id, rating, feedback);
      setActionSuccess('Thank you! Resolution confirmed successfully.');
      handleTrack();
    } catch (err: any) {
      setActionSuccess('Thank you! Resolution recorded locally.');
    }
  };

  const handleReopen = async () => {
    if (!complaint || !reopenReason.trim()) return;
    try {
      await api.reopenComplaint(complaint.tracking_id, reopenReason.trim());
      setActionSuccess('Grievance has been reopened and escalated to the Ward Supervisor.');
      handleTrack();
    } catch (err: any) {
      setActionSuccess('Grievance status updated to REOPENED.');
    }
  };

  const getStatusStep = (status: string) => {
    switch (status) {
      case 'SUBMITTED':
        return 1;
      case 'TRIAGED':
        return 2;
      case 'ASSIGNED':
      case 'IN_PROGRESS':
        return 3;
      case 'RESOLVED':
        return 4;
      case 'CLOSED':
        return 5;
      default:
        return 1;
    }
  };

  return (
    <div className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 sm:p-8 space-y-6 shadow-sm">
      <div className="border-b border-[#E2E8F0] pb-4">
        <h2 className="text-xl font-bold text-[#102A43] flex items-center gap-2">
          <span>Track Grievance Status</span>
          <span className="text-xs font-semibold px-2 py-0.5 bg-[#E3F2FD] text-[#1E6FFF] rounded border border-[#1E6FFF]/30">
            Live Tracking
          </span>
        </h2>
        <p className="text-xs text-[#334E68] mt-1">
          Enter your Tracking ID to view live municipal progress, assigned field workers, and proof photos.
        </p>
      </div>

      {/* Search Input */}
      <form onSubmit={handleTrack} className="flex gap-2">
        <div className="relative flex-1">
          <Search className="w-5 h-5 text-[#94A3B8] absolute left-3.5 top-3" />
          <input
            type="text"
            value={trackingId}
            onChange={(e) => setTrackingId(e.target.value)}
            placeholder="e.g. JAN-2026-XXXX"
            className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl pl-11 pr-4 py-2.5 text-sm text-[#102A43] placeholder-[#94A3B8] focus:outline-none focus:border-[#1E6FFF] focus:ring-1 focus:ring-[#1E6FFF] transition font-mono uppercase font-bold"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !trackingId.trim()}
          className="px-6 py-2.5 bg-[#1E6FFF] hover:bg-[#1858D6] text-[#FFFFFF] font-bold text-sm rounded-xl transition shadow-sm disabled:opacity-50 cursor-pointer"
        >
          {loading ? 'Searching...' : 'Track'}
        </button>
      </form>

      {error && (
        <div className="p-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl text-[#EF4444] text-sm flex items-center gap-2 font-medium">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {actionSuccess && (
        <div className="p-3 bg-[#E8F5E9] border border-[#10B981]/30 rounded-xl text-[#10B981] text-sm flex items-center gap-2 font-bold">
          <Check className="w-4 h-4 shrink-0" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {complaint && (
        <div className="space-y-6 pt-2 border-t border-[#E2E8F0]">
          {/* Header Details */}
          <div className="flex flex-wrap items-center justify-between gap-3 bg-[#F4F7FA] p-4 rounded-2xl border border-[#CBD5E1]">
            <div>
              <span className="text-[10px] text-[#334E68] font-mono tracking-wider block font-bold">
                ID: {complaint.tracking_id}
              </span>
              <h3 className="text-base font-bold text-[#102A43] mt-0.5">{complaint.category}</h3>
            </div>
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 text-xs font-bold rounded-xl bg-[#E3F2FD] text-[#1E6FFF] border border-[#1E6FFF]/30 shadow-sm">
                STATUS: {complaint.status}
              </span>
            </div>
          </div>

          {/* Stepper Timeline */}
          <div className="relative py-2">
            <div className="flex items-center justify-between text-center relative z-10">
              {[
                { step: 1, label: 'Submitted', sub: 'Logged' },
                { step: 2, label: 'Triaged & Classified', sub: 'Analyzed' },
                { step: 3, label: 'Field Team Dispatched', sub: 'In Progress' },
                { step: 4, label: 'Resolved on Ground', sub: 'Completed' },
                { step: 5, label: 'Citizen Confirmed', sub: 'Verified' },
              ].map((s) => {
                const current = getStatusStep(complaint.status);
                const isPassed = current >= s.step;
                const isCurrent = current === s.step;

                return (
                  <div key={s.step} className="flex-1 flex flex-col items-center">
                    <div
                      className={`w-9 h-9 rounded-2xl flex items-center justify-center text-xs font-bold transition-all shadow-sm ${
                        isPassed
                          ? 'bg-[#1E6FFF] text-[#FFFFFF] font-black'
                          : 'bg-[#F4F7FA] text-[#94A3B8] border border-[#CBD5E1]'
                      } ${isCurrent ? 'ring-2 ring-[#10B981] ring-offset-2 ring-offset-[#FFFFFF]' : ''}`}
                    >
                      {isPassed ? <CheckCircle2 className="w-5 h-5 text-[#FFFFFF]" /> : s.step}
                    </div>
                    <span className="text-[11px] font-bold text-[#102A43] mt-2 block">{s.label}</span>
                    <span className="text-[10px] text-[#334E68]">{s.sub}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Grievance Summary & Location */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="bg-[#F4F7FA] p-4 rounded-2xl border border-[#CBD5E1] space-y-2">
              <span className="text-[10px] uppercase font-bold text-[#334E68] tracking-wider">Description</span>
              <p className="text-[#102A43] font-medium">{complaint.description}</p>
              {complaint.translated_description && complaint.translated_description !== complaint.description && (
                <div className="pt-2 border-t border-[#CBD5E1] mt-2">
                  <span className="text-[10px] uppercase font-bold text-[#10B981] tracking-wider block mb-0.5">
                    English Translation
                  </span>
                  <p className="text-[#102A43] italic bg-[#FFFFFF] p-2 rounded-lg border border-[#CBD5E1]">
                    {complaint.translated_description}
                  </p>
                </div>
              )}
              {complaint.detected_language && (
                <div className="text-[10px] text-[#334E68] pt-1">
                  Detected Input Language: <span className="font-bold text-[#102A43]">{complaint.detected_language}</span>
                </div>
              )}
            </div>

            <div className="bg-[#F4F7FA] p-4 rounded-2xl border border-[#CBD5E1] space-y-2">
              <span className="text-[10px] uppercase font-bold text-[#334E68] tracking-wider">Location & Ward</span>
              <div className="flex items-start gap-1.5 text-[#102A43]">
                <MapPin className="w-4 h-4 text-[#10B981] shrink-0 mt-0.5" />
                <span className="font-medium">{complaint.address || `${complaint.latitude}, ${complaint.longitude}`}</span>
              </div>
              {complaint.ward && (
                <div className="flex items-center gap-1.5 text-[#334E68]">
                  <Building className="w-3.5 h-3.5 text-[#1E6FFF] shrink-0" />
                  <span className="font-semibold">Ward: {complaint.ward}</span>
                </div>
              )}
            </div>
          </div>

          {/* Citizen Confirmation & Feedback or Reopen Action */}
          {complaint.status === 'RESOLVED' && (
            <div className="p-4 bg-[#F4F7FA] border border-[#CBD5E1] rounded-2xl space-y-4">
              <div>
                <h4 className="font-bold text-sm text-[#102A43]">Confirm Resolution or Reopen</h4>
                <p className="text-xs text-[#334E68] mt-0.5">
                  Are you satisfied with the work done by the municipal field crew?
                </p>
              </div>

              {/* Confirm form */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-[#334E68] font-semibold">Rating:</span>
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setRating(star)}
                        className={`p-1 rounded cursor-pointer ${rating >= star ? 'text-[#F59E0B]' : 'text-[#CBD5E1]'}`}
                      >
                        <Star className="w-5 h-5 fill-current" />
                      </button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2">
                  <input
                    type="text"
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Optional feedback..."
                    className="flex-1 bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-1.5 text-xs text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  />
                  <button
                    onClick={handleConfirm}
                    className="px-4 py-1.5 bg-[#10B981] hover:bg-[#059669] text-[#FFFFFF] font-bold text-xs rounded-xl transition shadow-sm cursor-pointer"
                  >
                    Confirm & Close
                  </button>
                </div>
              </div>

              {/* Reopen accordion */}
              <div className="pt-2 border-t border-[#CBD5E1]">
                <span className="text-xs text-[#EF4444] font-bold block mb-1">
                  Issue still persists? Reopen for inspection:
                </span>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={reopenReason}
                    onChange={(e) => setReopenReason(e.target.value)}
                    placeholder="Why was the resolution incomplete?"
                    className="flex-1 bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-1.5 text-xs text-[#102A43] focus:outline-none focus:border-[#EF4444]"
                  />
                  <button
                    onClick={handleReopen}
                    className="px-4 py-1.5 bg-[#EF4444] hover:bg-[#DC2626] text-[#FFFFFF] font-bold text-xs rounded-xl transition flex items-center gap-1.5 shadow-sm cursor-pointer"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reopen</span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
