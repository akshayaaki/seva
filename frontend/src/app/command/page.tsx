'use client';

import React, { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import TriageMap from '@/components/TriageMap';
import IncidentFeed from '@/components/IncidentFeed';
import {
  Shield,
  RefreshCw,
  Radio,
  PlusCircle,
  Pencil,
  Trash2,
  Eye,
  CheckCircle2,
  AlertTriangle,
  MapPin,
  Clock,
  Layers,
  X,
  Loader2,
} from 'lucide-react';
import { Incident, PriorityLevel, IncidentStatus } from '@/types';
import { api } from '@/lib/api';

export default function CommandPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [loading, setLoading] = useState(true);

  // CRUD Modals State
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [editingIncident, setEditingIncident] = useState<Incident | null>(null);
  const [deletingIncident, setDeletingIncident] = useState<Incident | null>(null);
  const [inspectingIncident, setInspectingIncident] = useState<Incident | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  // Create Form State
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState('Roads & Potholes');
  const [newPriority, setNewPriority] = useState<PriorityLevel>('HIGH');
  const [newScore, setNewScore] = useState(75);
  const [newWard, setNewWard] = useState('Ward 12 (Bandra)');
  const [newAddress, setNewAddress] = useState('Linking Road, Bandra West, Mumbai');
  const [newLat, setNewLat] = useState(19.0596);
  const [newLon, setNewLon] = useState(72.8295);
  const [newDesc, setNewDesc] = useState('');

  // Edit Form State
  const [editTitle, setEditTitle] = useState('');
  const [editCategory, setEditCategory] = useState('');
  const [editPriority, setEditPriority] = useState<PriorityLevel>('MEDIUM');
  const [editScore, setEditScore] = useState(50);
  const [editStatus, setEditStatus] = useState<IncidentStatus>('OPEN');
  const [editWard, setEditWard] = useState('');
  const [editDesc, setEditDesc] = useState('');

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      const data = await api.getIncidents({ limit: 100 });
      setIncidents(data || []);
      if (data && data.length > 0) {
        if (!selectedIncident || !data.find((i) => i.id === selectedIncident.id)) {
          setSelectedIncident(data[0]);
        }
      } else {
        setSelectedIncident(null);
      }
    } catch (err: any) {
      console.error('API error fetching incidents:', err);
      setIncidents([]);
      setSelectedIncident(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIncidents();
  }, []);

  // Handle Create Submit
  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) {
      setModalError('Incident title is required.');
      return;
    }
    setActionLoading(true);
    setModalError(null);
    try {
      await api.createIncident({
        title: newTitle.trim(),
        description: newDesc.trim() || newTitle.trim(),
        category: newCategory,
        priority_level: newPriority.toLowerCase(),
        priority_score: newScore,
        status: 'open',
        latitude: Number(newLat) || 19.0760,
        longitude: Number(newLon) || 72.8777,
        address: newAddress.trim() || 'Reported Location',
        ward_id: newWard,
      });
      setIsCreateOpen(false);
      setNewTitle('');
      setNewDesc('');
      await fetchIncidents();
    } catch (err: any) {
      setModalError(err.message || 'Failed to create incident.');
    } finally {
      setActionLoading(false);
    }
  };

  // Open Edit Modal
  const handleOpenEdit = (inc: Incident) => {
    setEditingIncident(inc);
    setEditTitle(inc.title);
    setEditCategory(inc.category);
    setEditPriority(inc.priority_level);
    setEditScore(Math.round(inc.priority_score));
    setEditStatus(inc.status);
    setEditWard(inc.ward || 'Ward 12');
    setEditDesc(inc.summary || '');
    setModalError(null);
  };

  // Handle Edit Submit
  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingIncident) return;
    setActionLoading(true);
    setModalError(null);
    try {
      await api.updateIncident(editingIncident.id, {
        title: editTitle.trim(),
        description: editDesc.trim(),
        category: editCategory,
        priority_level: editPriority.toLowerCase(),
        priority_score: Number(editScore),
        status: editStatus.toLowerCase(),
        ward_id: editWard,
      });
      setEditingIncident(null);
      await fetchIncidents();
    } catch (err: any) {
      setModalError(err.message || 'Failed to update incident.');
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Delete Confirm
  const handleDeleteConfirm = async () => {
    if (!deletingIncident) return;
    setActionLoading(true);
    try {
      await api.deleteIncident(deletingIncident.id);
      setDeletingIncident(null);
      if (selectedIncident?.id === deletingIncident.id) {
        setSelectedIncident(null);
      }
      await fetchIncidents();
    } catch (err: any) {
      console.error('Delete failed:', err);
    } finally {
      setActionLoading(false);
    }
  };

  const getPriorityBadgeClass = (level: PriorityLevel) => {
    switch (level) {
      case 'CRITICAL':
        return 'bg-[#EF4444]/10 text-[#EF4444] border-[#EF4444]/30';
      case 'HIGH':
        return 'bg-[#F59E0B]/10 text-[#F59E0B] border-[#F59E0B]/30';
      case 'MEDIUM':
        return 'bg-[#E3F2FD] text-[#1E6FFF] border-[#1E6FFF]/30';
      case 'LOW':
        return 'bg-[#E8F5E9] text-[#10B981] border-[#10B981]/30';
      default:
        return 'bg-[#F4F7FA] text-[#334E68] border-[#CBD5E1]';
    }
  };

  return (
    <div className="min-h-screen bg-[#F4F7FA] text-[#102A43] flex flex-col selection:bg-[#1E6FFF] selection:text-[#FFFFFF]">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* Header */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#E2E8F0] pb-4">
          <div>
            <div className="flex items-center gap-2">
              <Shield className="w-6 h-6 text-[#1E6FFF]" />
              <h1 className="text-2xl font-black text-[#102A43] tracking-tight">
                Municipal Command Center & Triage
              </h1>
              <span className="flex items-center gap-1.5 px-3 py-0.5 rounded-full bg-[#E8F5E9] border border-[#10B981]/30 text-[#10B981] text-xs font-bold shadow-sm">
                <Radio className="w-3 h-3 text-[#10B981] animate-pulse" />
                Live Feed
              </span>
            </div>
            <p className="text-xs text-[#334E68] mt-1 font-medium">
              GIS real-time situational awareness, clustered incident queue, and AI-driven field dispatch.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setIsCreateOpen(true);
                setModalError(null);
              }}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#10B981] hover:bg-[#0D9468] text-xs font-bold text-[#FFFFFF] transition shadow-sm cursor-pointer"
            >
              <PlusCircle className="w-4 h-4 text-[#FFFFFF]" />
              <span>Log New Incident</span>
            </button>
            <button
              onClick={fetchIncidents}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[#1E6FFF] hover:bg-[#1858D6] text-xs font-bold text-[#FFFFFF] transition shadow-sm cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Queue</span>
            </button>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Map Column */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between text-xs text-[#334E68]">
              <span className="font-bold text-[#102A43]">GIS Heat & Cluster Map</span>
              <span>Click markers to inspect & dispatch</span>
            </div>
            <TriageMap
              incidents={incidents}
              selectedIncident={selectedIncident}
              onSelectIncident={(inc) => setSelectedIncident(inc)}
            />
          </div>

          {/* Incident Feed Column */}
          <div className="lg:col-span-5 space-y-3">
            <div className="flex items-center justify-between text-xs text-[#334E68]">
              <span className="font-bold text-[#102A43]">
                Active Incidents Queue ({incidents.length})
              </span>
              <span>Sorted by AI Priority Score</span>
            </div>
            <IncidentFeed
              incidents={incidents}
              selectedIncident={selectedIncident}
              onSelectIncident={(inc) => setSelectedIncident(inc)}
              onRefresh={fetchIncidents}
              onEditIncident={handleOpenEdit}
              onDeleteIncident={(inc) => setDeletingIncident(inc)}
              onInspectIncident={(inc) => setInspectingIncident(inc)}
            />
          </div>
        </div>
      </main>

      {/* CREATE MODAL */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-[#102A43]/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <div className="flex items-center gap-2">
                <PlusCircle className="w-5 h-5 text-[#10B981]" />
                <h3 className="text-lg font-bold text-[#102A43]">Log Municipal Incident</h3>
              </div>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="text-[#334E68] hover:text-[#102A43] cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="p-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl text-xs text-[#EF4444] font-medium">
                {modalError}
              </div>
            )}

            <form onSubmit={handleCreateSubmit} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="font-bold text-[#102A43]">Incident Title *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Major Water Pipeline Leak near SV Road"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-[#102A43]">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  >
                    <option value="Roads & Potholes">Roads & Potholes</option>
                    <option value="Solid Waste & Sanitation">Solid Waste & Sanitation</option>
                    <option value="Water Supply & Sewage">Water Supply & Sewage</option>
                    <option value="Stormwater Drainage">Stormwater Drainage</option>
                    <option value="Street Lighting & Electrical">Street Lighting & Electrical</option>
                    <option value="Public Health & Vector">Public Health & Vector</option>
                    <option value="Civil Infrastructure">Civil Infrastructure</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-bold text-[#102A43]">Priority Level</label>
                  <select
                    value={newPriority}
                    onChange={(e) => {
                      const p = e.target.value as PriorityLevel;
                      setNewPriority(p);
                      if (p === 'CRITICAL') setNewScore(95);
                      else if (p === 'HIGH') setNewScore(80);
                      else if (p === 'MEDIUM') setNewScore(55);
                      else setNewScore(30);
                    }}
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  >
                    <option value="CRITICAL">Critical Priority</option>
                    <option value="HIGH">High Urgency</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-[#102A43]">Ward Zone</label>
                  <input
                    type="text"
                    value={newWard}
                    onChange={(e) => setNewWard(e.target.value)}
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-[#102A43]">Priority Score (0-100)</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={newScore}
                    onChange={(e) => setNewScore(Number(e.target.value))}
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-bold text-[#102A43]">Location Address</label>
                <input
                  type="text"
                  value={newAddress}
                  onChange={(e) => setNewAddress(e.target.value)}
                  className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-[#102A43]">Latitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={newLat}
                    onChange={(e) => setNewLat(Number(e.target.value))}
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-[#102A43]">Longitude</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={newLon}
                    onChange={(e) => setNewLon(Number(e.target.value))}
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-bold text-[#102A43]">Description & Dispatch Details</label>
                <textarea
                  rows={2}
                  placeholder="Detailed field description..."
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="flex-1 py-2.5 bg-[#10B981] hover:bg-[#0D9468] text-[#FFFFFF] font-bold rounded-xl transition shadow-sm flex items-center justify-center gap-2 cursor-pointer"
                >
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <PlusCircle className="w-4 h-4" />}
                  <span>Save & Dispatch to Triage</span>
                </button>
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2.5 bg-[#F4F7FA] text-[#334E68] font-bold rounded-xl border border-[#CBD5E1] hover:bg-[#E2E8F0] cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* EDIT MODAL */}
      {editingIncident && (
        <div className="fixed inset-0 z-50 bg-[#102A43]/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl max-w-lg w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <div className="flex items-center gap-2">
                <Pencil className="w-5 h-5 text-[#1E6FFF]" />
                <div>
                  <h3 className="text-lg font-bold text-[#102A43]">Edit Incident</h3>
                  <span className="text-[10px] text-[#334E68] font-mono">{editingIncident.incident_number}</span>
                </div>
              </div>
              <button
                onClick={() => setEditingIncident(null)}
                className="text-[#334E68] hover:text-[#102A43] cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {modalError && (
              <div className="p-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl text-xs text-[#EF4444] font-medium">
                {modalError}
              </div>
            )}

            <form onSubmit={handleEditSubmit} className="space-y-4 text-xs">
              <div className="space-y-1">
                <label className="font-bold text-[#102A43]">Incident Title</label>
                <input
                  type="text"
                  required
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-[#102A43]">Status</label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value as IncidentStatus)}
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  >
                    <option value="OPEN">Open</option>
                    <option value="TRIAGED">Triaged</option>
                    <option value="ASSIGNED">Assigned</option>
                    <option value="IN_PROGRESS">In Progress</option>
                    <option value="RESOLVED">Resolved</option>
                    <option value="CLOSED">Closed</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="font-bold text-[#102A43]">Priority Level</label>
                  <select
                    value={editPriority}
                    onChange={(e) => setEditPriority(e.target.value as PriorityLevel)}
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  >
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="font-bold text-[#102A43]">Priority Score (0-100)</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={editScore}
                    onChange={(e) => setEditScore(Number(e.target.value))}
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  />
                </div>
                <div className="space-y-1">
                  <label className="font-bold text-[#102A43]">Ward</label>
                  <input
                    type="text"
                    value={editWard}
                    onChange={(e) => setEditWard(e.target.value)}
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="font-bold text-[#102A43]">Description & Field Notes</label>
                <textarea
                  rows={3}
                  value={editDesc}
                  onChange={(e) => setEditDesc(e.target.value)}
                  className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-2 text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                />
              </div>

              <div className="flex items-center gap-3 pt-2">
                <button
                  type="submit"
                  disabled={actionLoading}
                  className="flex-1 py-2.5 bg-[#1E6FFF] hover:bg-[#1858D6] text-[#FFFFFF] font-bold rounded-xl transition shadow-sm flex items-center justify-center gap-2 cursor-pointer"
                >
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                  <span>Save Changes</span>
                </button>
                <button
                  type="button"
                  onClick={() => setEditingIncident(null)}
                  className="px-4 py-2.5 bg-[#F4F7FA] text-[#334E68] font-bold rounded-xl border border-[#CBD5E1] hover:bg-[#E2E8F0] cursor-pointer"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* INSPECT DETAILS MODAL */}
      {inspectingIncident && (
        <div className="fixed inset-0 z-50 bg-[#102A43]/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl max-w-lg w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in duration-150">
            <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
              <div className="flex items-center gap-2">
                <Eye className="w-5 h-5 text-[#1E6FFF]" />
                <div>
                  <h3 className="text-lg font-bold text-[#102A43]">Incident Telemetry</h3>
                  <span className="text-[10px] text-[#334E68] font-mono">{inspectingIncident.incident_number}</span>
                </div>
              </div>
              <button
                onClick={() => setInspectingIncident(null)}
                className="text-[#334E68] hover:text-[#102A43] cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs">
              <div className="flex items-center justify-between bg-[#F4F7FA] border border-[#E2E8F0] p-3 rounded-2xl">
                <div>
                  <span className="text-[10px] uppercase font-bold text-[#334E68] block">Live Status</span>
                  <span className="text-sm font-black text-[#102A43]">{inspectingIncident.status}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] uppercase font-bold text-[#334E68] block">Priority</span>
                  <span className={`px-2.5 py-0.5 rounded-lg border font-bold ${getPriorityBadgeClass(inspectingIncident.priority_level)}`}>
                    {inspectingIncident.priority_level} ({Math.round(inspectingIncident.priority_score)})
                  </span>
                </div>
              </div>

              <div className="space-y-1.5">
                <span className="text-[10px] uppercase font-bold text-[#334E68]">Incident Summary</span>
                <h4 className="text-sm font-bold text-[#102A43]">{inspectingIncident.title}</h4>
                {inspectingIncident.summary && inspectingIncident.summary !== inspectingIncident.title && (
                  <p className="text-[#334E68] bg-[#F4F7FA] p-2.5 rounded-xl border border-[#E2E8F0]">
                    {inspectingIncident.summary}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-2.5 bg-[#F4F7FA] rounded-xl border border-[#E2E8F0] space-y-0.5">
                  <span className="text-[10px] uppercase font-bold text-[#334E68] flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-[#10B981]" /> Location
                  </span>
                  <p className="font-semibold text-[#102A43] truncate">{inspectingIncident.address || inspectingIncident.ward || 'Mumbai Area'}</p>
                  <p className="text-[10px] text-[#334E68] font-mono">{inspectingIncident.latitude.toFixed(4)}, {inspectingIncident.longitude.toFixed(4)}</p>
                </div>

                <div className="p-2.5 bg-[#F4F7FA] rounded-xl border border-[#E2E8F0] space-y-0.5">
                  <span className="text-[10px] uppercase font-bold text-[#334E68] flex items-center gap-1">
                    <Layers className="w-3 h-3 text-[#1E6FFF]" /> Clustered Signals
                  </span>
                  <p className="font-semibold text-[#102A43]">{inspectingIncident.complaint_count} Citizen Submissions</p>
                  <p className="text-[10px] text-[#334E68]">Geo-fenced within 500m</p>
                </div>
              </div>

              <div className="flex items-center justify-between text-[11px] text-[#334E68] border-t border-[#E2E8F0] pt-3">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" /> Registered: {new Date(inspectingIncident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
                <button
                  onClick={() => {
                    const inc = inspectingIncident;
                    setInspectingIncident(null);
                    handleOpenEdit(inc);
                  }}
                  className="px-3 py-1.5 bg-[#1E6FFF] hover:bg-[#1858D6] text-[#FFFFFF] font-bold rounded-xl flex items-center gap-1.5 cursor-pointer shadow-sm"
                >
                  <Pencil className="w-3.5 h-3.5" /> Edit Incident
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* DELETE MODAL */}
      {deletingIncident && (
        <div className="fixed inset-0 z-50 bg-[#102A43]/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl max-w-md w-full p-6 space-y-4 shadow-2xl animate-in fade-in zoom-in duration-150">
            <div className="w-12 h-12 bg-[#EF4444]/10 text-[#EF4444] rounded-2xl flex items-center justify-center mx-auto border border-[#EF4444]/30">
              <AlertTriangle className="w-6 h-6 text-[#EF4444]" />
            </div>

            <div className="text-center space-y-1">
              <h3 className="text-lg font-bold text-[#102A43]">Archive / Delete Incident</h3>
              <p className="text-xs text-[#334E68]">
                Are you sure you want to delete incident <span className="font-mono font-bold text-[#102A43]">{deletingIncident.incident_number}</span>? This will close all associated active triage queues.
              </p>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                onClick={handleDeleteConfirm}
                disabled={actionLoading}
                className="flex-1 py-2.5 bg-[#EF4444] hover:bg-[#DC2626] text-[#FFFFFF] font-bold rounded-xl transition shadow-sm flex items-center justify-center gap-2 cursor-pointer"
              >
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                <span>Confirm Delete</span>
              </button>
              <button
                onClick={() => setDeletingIncident(null)}
                className="px-4 py-2.5 bg-[#F4F7FA] text-[#334E68] font-bold rounded-xl border border-[#CBD5E1] hover:bg-[#E2E8F0] cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


