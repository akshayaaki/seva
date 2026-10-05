'use client';

import React, { useState, useEffect } from 'react';
import {
  Navigation,
  Camera,
  MapPin,
  Check,
  Truck,
  ShieldCheck,
} from 'lucide-react';
import { WorkerTask, TaskStatus } from '@/types';
import { api } from '@/lib/api';

export default function WorkerPortal() {
  const [tasks, setTasks] = useState<WorkerTask[]>([]);
  const [workers, setWorkers] = useState<any[]>([]);
  const [selectedWorkerId, setSelectedWorkerId] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState<WorkerTask | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');
  const [afterPhoto, setAfterPhoto] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const fetchWorkers = async () => {
    try {
      const data = await api.getWorkers();
      if (data && data.length > 0) {
        setWorkers(data);
      }
    } catch {
      // Fallback
    }
  };

  const fetchTasks = async (workerId?: string) => {
    try {
      setLoading(true);
      const targetWorker = workerId !== undefined ? workerId : selectedWorkerId;
      const data = await api.getWorkerTasks(targetWorker !== 'all' ? targetWorker : undefined);
      setTasks(data || []);
      if (data && data.length > 0) {
        if (!selectedTask || !data.find((t) => t.id === selectedTask.id)) {
          setSelectedTask(data[0]);
        }
      } else {
        setSelectedTask(null);
      }
    } catch (err) {
      console.error('Failed to fetch worker tasks:', err);
      setTasks([]);
      setSelectedTask(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkers();
    fetchTasks('all');
  }, []);

  const handleWorkerChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedWorkerId(val);
    fetchTasks(val);
  };

  const currentWorkerObj = workers.find((w) => w.id === selectedWorkerId);
  const currentUnitName =
    selectedWorkerId === 'all'
      ? 'All Municipal Response Units'
      : currentWorkerObj?.user_profiles?.full_name
      ? `${currentWorkerObj.user_profiles.full_name} (${currentWorkerObj.employee_code || 'Rapid Response'})`
      : 'Rapid Response Crew Alpha';

  const currentDeptName = currentWorkerObj?.departments?.name || 'Rapid Response & Infrastructure Operations';

  const handleStatusTransition = async (newStatus: TaskStatus) => {
    if (!selectedTask) return;
    setUpdating(true);
    setMessage(null);

    try {
      await api.updateTaskStatus(selectedTask.id, newStatus, {
        notes: resolutionNotes || undefined,
        evidence_url: afterPhoto || undefined,
        latitude: selectedTask.latitude,
        longitude: selectedTask.longitude,
      });

      setMessage(`Task status updated to: ${newStatus}`);
      fetchTasks();
    } catch (err: any) {
      setMessage(`Task updated locally to: ${newStatus}`);
      setSelectedTask((prev) => (prev ? { ...prev, status: newStatus } : null));
    } finally {
      setUpdating(false);
    }
  };

  const handlePhotoCapture = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setAfterPhoto(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  return (
    <div className="space-y-6">
      {/* Mobile-Friendly Worker Header */}
      <div className="bg-[#FFFFFF] border border-[#E2E8F0] p-4 rounded-3xl flex flex-wrap items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-[#1E6FFF] text-[#FFFFFF] flex items-center justify-center font-bold shadow-sm">
            <Truck className="w-6 h-6" />
          </div>
          <div>
            <span className="text-[10px] text-[#334E68] uppercase tracking-wider block font-bold">
              {currentDeptName}
            </span>
            <h2 className="text-base font-bold text-[#102A43]">{currentUnitName}</h2>
            <span className="text-xs text-[#10B981] font-bold flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-[#10B981] animate-pulse" />
              On-Duty • Real-time GPS Tracked
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Unit Selector */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-[#334E68]">Active Unit:</span>
            <select
              value={selectedWorkerId}
              onChange={handleWorkerChange}
              className="text-xs bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3 py-1.5 text-[#102A43] font-medium focus:outline-none focus:border-[#1E6FFF]"
            >
              <option value="all">All Field Units & Tasks</option>
              {workers.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.user_profiles?.full_name || 'Crew Worker'} ({w.employee_code || 'Unit'} - {w.departments?.name || 'Municipal'})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => fetchTasks()}
            disabled={loading}
            className="px-3.5 py-1.5 bg-[#E3F2FD] hover:bg-[#D0E7FC] rounded-xl text-xs font-bold text-[#1E6FFF] border border-[#1E6FFF]/30 flex items-center gap-1.5 cursor-pointer transition shadow-sm"
          >
            <span>Active Tasks ({tasks.length})</span>
          </button>
        </div>
      </div>

      {message && (
        <div className="p-3 bg-[#E8F5E9] border border-[#10B981]/30 rounded-2xl text-[#10B981] text-xs font-bold flex items-center gap-2">
          <Check className="w-4 h-4 shrink-0" />
          <span>{message}</span>
        </div>
      )}

      {/* Main Layout: Task List & Detail Action Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Task List */}
        <div className="lg:col-span-5 space-y-3">
          <span className="text-xs font-bold text-[#102A43] uppercase tracking-wider block">
            Assigned Work Orders
          </span>
          {tasks.length === 0 ? (
            <div className="text-center py-10 bg-[#FFFFFF] border border-[#E2E8F0] rounded-2xl text-[#334E68] text-xs font-medium p-4">
              No field work orders currently assigned.
            </div>
          ) : (
            tasks.map((task) => {
              const isSelected = selectedTask?.id === task.id;
              return (
                <div
                  key={task.id}
                  onClick={() => setSelectedTask(task)}
                  className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-[#E3F2FD] border-[#1E6FFF] shadow-md ring-2 ring-[#1E6FFF]'
                      : 'bg-[#FFFFFF] border-[#E2E8F0] hover:border-[#1E6FFF] hover:bg-[#F4F7FA]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-mono font-bold text-[#334E68]">{task.task_number}</span>
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-lg bg-[#E8F5E9] text-[#10B981] border border-[#10B981]/30">
                      {task.status}
                    </span>
                  </div>
                  <h3 className="text-sm font-bold text-[#102A43] mt-1">{task.title}</h3>
                  <div className="flex items-center gap-1.5 text-xs text-[#334E68] mt-2">
                    <MapPin className="w-3.5 h-3.5 text-[#10B981] shrink-0" />
                    <span className="truncate font-medium">{task.address}</span>
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Right: Detailed Execution Card */}
        <div className="lg:col-span-7">
          {selectedTask ? (
            <div className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 space-y-6 shadow-sm">
              <div className="border-b border-[#E2E8F0] pb-4 flex items-start justify-between">
                <div>
                  <span className="text-xs font-mono text-[#1E6FFF] font-bold">
                    {selectedTask.task_number}
                  </span>
                  <h2 className="text-lg font-bold text-[#102A43] mt-1">{selectedTask.title}</h2>
                  <p className="text-xs text-[#334E68] mt-1 font-medium">{selectedTask.description}</p>
                </div>
                <span className="px-3 py-1 rounded-xl text-xs font-bold bg-[#E3F2FD] text-[#1E6FFF] border border-[#1E6FFF]/30">
                  {selectedTask.priority_level}
                </span>
              </div>

              {/* Location & Navigation */}
              <div className="bg-[#F4F7FA] p-4 rounded-2xl border border-[#CBD5E1] flex items-center justify-between">
                <div className="space-y-1">
                  <span className="text-[10px] uppercase font-bold text-[#334E68] tracking-wider">
                    Site Location
                  </span>
                  <p className="text-xs text-[#102A43] font-semibold">{selectedTask.address}</p>
                </div>
                <a
                  href={`https://www.google.com/maps/dir/?api=1&destination=${selectedTask.latitude},${selectedTask.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 px-3.5 py-2 bg-[#1E6FFF] hover:bg-[#1858D6] text-[#FFFFFF] font-bold text-xs rounded-xl shadow-sm transition"
                >
                  <Navigation className="w-3.5 h-3.5" />
                  <span>Navigate</span>
                </a>
              </div>

              {/* Workflow Actions */}
              <div className="space-y-4">
                <span className="text-xs font-bold text-[#102A43] uppercase tracking-wider block">
                  Operations Execution Pipeline
                </span>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <button
                    onClick={() => handleStatusTransition('ACCEPTED')}
                    disabled={updating || selectedTask.status !== 'PENDING'}
                    className="p-2.5 rounded-xl border border-[#CBD5E1] bg-[#F4F7FA] hover:bg-[#E3F2FD] hover:text-[#1E6FFF] text-xs font-bold text-[#102A43] disabled:opacity-40 transition shadow-sm cursor-pointer"
                  >
                    1. Accept
                  </button>

                  <button
                    onClick={() => handleStatusTransition('EN_ROUTE')}
                    disabled={updating || selectedTask.status === 'EN_ROUTE'}
                    className="p-2.5 rounded-xl border border-[#CBD5E1] bg-[#F4F7FA] text-[#102A43] hover:bg-[#E3F2FD] hover:text-[#1E6FFF] text-xs font-bold disabled:opacity-40 transition shadow-sm cursor-pointer"
                  >
                    2. En Route
                  </button>

                  <button
                    onClick={() => handleStatusTransition('ON_SCENE')}
                    disabled={updating || selectedTask.status === 'ON_SCENE'}
                    className="p-2.5 rounded-xl border border-[#CBD5E1] bg-[#F4F7FA] text-[#102A43] hover:bg-[#E3F2FD] hover:text-[#1E6FFF] text-xs font-bold disabled:opacity-40 transition shadow-sm cursor-pointer"
                  >
                    3. On Scene
                  </button>

                  <button
                    onClick={() => handleStatusTransition('IN_PROGRESS')}
                    disabled={updating || selectedTask.status === 'IN_PROGRESS'}
                    className="p-2.5 rounded-xl border border-[#CBD5E1] bg-[#F4F7FA] text-[#102A43] hover:bg-[#E3F2FD] hover:text-[#1E6FFF] text-xs font-bold disabled:opacity-40 transition shadow-sm cursor-pointer"
                  >
                    4. Work Active
                  </button>
                </div>
              </div>

              {/* Completion & Proof Form */}
              <div className="p-4 bg-[#F4F7FA] border border-[#CBD5E1] rounded-2xl space-y-4">
                <span className="text-xs font-bold text-[#102A43] uppercase tracking-wider flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-[#10B981]" />
                  Field Completion Proof & Verification
                </span>

                <div>
                  <label className="block text-xs font-bold text-[#102A43] mb-1">
                    Completion Notes / Work Performed
                  </label>
                  <textarea
                    rows={2}
                    value={resolutionNotes}
                    onChange={(e) => setResolutionNotes(e.target.value)}
                    placeholder="e.g. Cleared 200m drain using vacuum suction, debris hauled to landfill..."
                    className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl p-2.5 text-xs text-[#102A43] focus:outline-none focus:border-[#1E6FFF]"
                  />
                </div>

                <div className="flex items-center gap-4">
                  <label className="cursor-pointer flex items-center gap-2 px-3.5 py-2 bg-[#FFFFFF] border border-dashed border-[#CBD5E1] hover:border-[#1E6FFF] rounded-xl text-xs font-bold text-[#1E6FFF]">
                    <Camera className="w-4 h-4 text-[#1E6FFF]" />
                    <span>Upload After-Resolution Photo</span>
                    <input
                      type="file"
                      accept="image/*"
                      capture="environment"
                      onChange={handlePhotoCapture}
                      className="hidden"
                    />
                  </label>

                  {afterPhoto && (
                    <img
                      src={afterPhoto}
                      alt="Work Proof"
                      className="w-12 h-12 rounded-xl object-cover border border-[#1E6FFF]"
                    />
                  )}
                </div>

                <button
                  onClick={() => handleStatusTransition('COMPLETED')}
                  disabled={updating}
                  className="w-full py-3 bg-[#10B981] hover:bg-[#059669] text-[#FFFFFF] font-bold text-xs uppercase tracking-wider rounded-xl shadow-sm transition cursor-pointer"
                >
                  {updating ? 'Verifying & Submitting...' : 'Mark Task as Completed & Notify Citizen'}
                </button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl text-[#334E68] text-xs">
              Select a task from the list to begin field operations.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
