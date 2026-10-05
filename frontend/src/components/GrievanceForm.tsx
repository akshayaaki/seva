'use client';

import React, { useState } from 'react';
import { Send, Check, AlertCircle, Copy, CheckCircle, Camera, Languages, Sparkles, Loader2 } from 'lucide-react';
import VoiceRecorder from './VoiceRecorder';
import LocationPicker from './LocationPicker';
import { api } from '@/lib/api';
import { Complaint } from '@/types';

interface GrievanceFormProps {
  onSuccess: (complaint: Complaint) => void;
}

const CATEGORIES = [
  'Roads & Potholes',
  'Garbage & Sanitation',
  'Drainage & Sewage Overflow',
  'Water Supply Disruption',
  'Street Lights Fault',
  'Stray Animals & Vector Control',
  'Public Health & Mosquitoes',
  'Illegal Encroachment',
  'Electrical Hazard',
];

export default function GrievanceForm({ onSuccess }: GrievanceFormProps) {
  const [citizenName, setCitizenName] = useState('');
  const [citizenPhone, setCitizenPhone] = useState('');
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [description, setDescription] = useState('');
  const [translatedDescription, setTranslatedDescription] = useState('');
  const [detectedLanguage, setDetectedLanguage] = useState<string | null>(null);
  const [isTranslating, setIsTranslating] = useState(false);
  const [ward, setWard] = useState('');
  const [address, setAddress] = useState('');
  const [coords, setCoords] = useState<{ latitude: number; longitude: number }>({
    latitude: 19.0760,
    longitude: 72.8777,
  });
  const [mediaPreview, setMediaPreview] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submittedComplaint, setSubmittedComplaint] = useState<Complaint | null>(null);
  const [copied, setCopied] = useState(false);

  const handleTranslate = async (overrideText?: string) => {
    const textToTranslate = overrideText !== undefined ? overrideText : description;
    if (!textToTranslate || !textToTranslate.trim()) return;

    setIsTranslating(true);
    try {
      const res = await api.translateGrievance(textToTranslate.trim());
      if (res.translated_text) {
        setTranslatedDescription(res.translated_text);
        if (res.language_name || res.detected_language) {
          setDetectedLanguage(res.language_name || res.detected_language);
        }
      }
    } catch (err) {
      console.error('Translation error:', err);
    } finally {
      setIsTranslating(false);
    }
  };

  const handleVoiceTranscription = (text: string) => {
    const updated = description ? `${description} ${text}` : text;
    setDescription(updated);
    handleTranslate(updated);
  };

  const handleLocationUpdate = (loc: {
    latitude: number;
    longitude: number;
    address: string;
    ward?: string;
  }) => {
    setCoords({ latitude: loc.latitude, longitude: loc.longitude });
    setAddress(loc.address);
    if (loc.ward) setWard(loc.ward);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setMediaPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!description.trim()) {
      setError('Please provide a description of the issue.');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        citizen_name: citizenName.trim() || undefined,
        citizen_phone: citizenPhone.trim() || undefined,
        description: `[${category}] ${description.trim()}`,
        latitude: coords.latitude,
        longitude: coords.longitude,
        address: address.trim() || undefined,
        ward: ward.trim() || undefined,
        media_urls: mediaPreview ? [mediaPreview] : [],
      };

      const result = await api.submitComplaint(payload);
      if (translatedDescription) {
        result.translated_description = translatedDescription;
      }
      setSubmittedComplaint(result);
      onSuccess(result);
    } catch (err: any) {
      console.error('Submission failed:', err);
      setError(err.message || 'Failed to submit grievance. Please check your network and try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const copyTrackingId = () => {
    if (submittedComplaint?.tracking_id) {
      navigator.clipboard.writeText(submittedComplaint.tracking_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  };

  if (submittedComplaint) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 sm:p-8 text-center space-y-5 shadow-sm">
        <div className="w-16 h-16 bg-[#E8F5E9] text-[#10B981] rounded-2xl flex items-center justify-center mx-auto border border-[#10B981]/30 shadow-sm">
          <CheckCircle className="w-9 h-9 text-[#10B981]" />
        </div>

        <div className="space-y-2">
          <span className="text-xs uppercase font-bold tracking-wider text-[#10B981] bg-[#E8F5E9] px-3 py-1 rounded-full border border-[#10B981]/30">
            Grievance Registered Successfully
          </span>
          <h3 className="text-2xl font-bold text-[#102A43]">Your Grievance Has Been Logged</h3>
          <p className="text-[#334E68] text-sm max-w-md mx-auto">
            Your grievance has been ingested by the Janseva AI engine, geolocated, and routed to the municipal field command for triage.
          </p>
        </div>

        {/* Tracking ID Card */}
        <div className="max-w-md mx-auto bg-[#F4F7FA] border border-[#CBD5E1] rounded-2xl p-4 flex items-center justify-between shadow-inner">
          <div className="text-left">
            <span className="text-[10px] text-[#334E68] uppercase tracking-wider block font-semibold">
              Tracking Reference Number
            </span>
            <span className="text-lg font-mono font-bold text-[#1E6FFF]">
              {submittedComplaint.tracking_id}
            </span>
          </div>
          <button
            onClick={copyTrackingId}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-[#1E6FFF] hover:bg-[#1858D6] text-[#FFFFFF] text-xs font-bold transition shadow-sm cursor-pointer"
          >
            {copied ? <Check className="w-4 h-4 text-[#FFFFFF]" /> : <Copy className="w-4 h-4" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        </div>

        <div className="pt-2">
          <button
            onClick={() => setSubmittedComplaint(null)}
            className="text-xs text-[#1E6FFF] hover:underline font-bold cursor-pointer"
          >
            File Another Grievance
          </button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="bg-[#FFFFFF] border border-[#E2E8F0] rounded-3xl p-6 sm:p-8 space-y-6 shadow-sm">
      <div className="border-b border-[#E2E8F0] pb-4">
        <h2 className="text-xl font-bold text-[#102A43] flex items-center gap-2">
          <span>File a Municipal Grievance</span>
          <span className="text-xs font-semibold px-2 py-0.5 bg-[#E3F2FD] text-[#1E6FFF] rounded border border-[#1E6FFF]/30">
            Citizen Portal
          </span>
        </h2>
        <p className="text-xs text-[#334E68] mt-1">
          Submit issues related to roads, sanitation, water, streetlights, or safety. Janseva AI immediately assigns municipal teams.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl flex items-center gap-3 text-[#EF4444] text-sm font-medium">
          <AlertCircle className="w-5 h-5 shrink-0 text-[#EF4444]" />
          <span>{error}</span>
        </div>
      )}

      {/* Citizen Basic Info */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-bold text-[#102A43] mb-1">
            Your Name <span className="text-[#334E68] font-normal">(Optional)</span>
          </label>
          <input
            type="text"
            value={citizenName}
            onChange={(e) => setCitizenName(e.target.value)}
            placeholder="e.g. Ramesh Sharma"
            className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3.5 py-2.5 text-sm text-[#102A43] placeholder-[#94A3B8] focus:outline-none focus:border-[#1E6FFF] focus:ring-1 focus:ring-[#1E6FFF] transition"
          />
        </div>

        <div>
          <label className="block text-xs font-bold text-[#102A43] mb-1">
            Mobile Number <span className="text-[#334E68] font-normal">(for SMS status updates)</span>
          </label>
          <input
            type="tel"
            value={citizenPhone}
            onChange={(e) => setCitizenPhone(e.target.value)}
            placeholder="e.g. +91 98765 43210"
            className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3.5 py-2.5 text-sm text-[#102A43] placeholder-[#94A3B8] focus:outline-none focus:border-[#1E6FFF] focus:ring-1 focus:ring-[#1E6FFF] transition"
          />
        </div>
      </div>

      {/* Category */}
      <div>
        <label className="block text-xs font-bold text-[#102A43] mb-1">
          Category <span className="text-[#EF4444]">*</span>
        </label>
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3.5 py-2.5 text-sm text-[#102A43] focus:outline-none focus:border-[#1E6FFF] focus:ring-1 focus:ring-[#1E6FFF] transition font-medium"
        >
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      {/* Voice Recorder Integration */}
      <div>
        <label className="block text-xs font-bold text-[#102A43] mb-1.5">
          Voice Input / Speak Grievance
        </label>
        <VoiceRecorder onTranscription={handleVoiceTranscription} />
      </div>

      {/* Description Textarea with English Translation */}
      <div className="space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <label className="text-xs font-bold text-[#102A43]">
            Grievance Description <span className="text-[#EF4444]">*</span>
          </label>
          <button
            type="button"
            onClick={() => handleTranslate()}
            disabled={isTranslating || !description.trim()}
            className="flex items-center gap-1.5 px-3 py-1 rounded-xl bg-[#E8F5E9] hover:bg-[#D1FAE5] text-[#10B981] text-xs font-bold transition disabled:opacity-50 border border-[#10B981]/30 shadow-xs cursor-pointer"
            title="Translate regional language text to English"
          >
            {isTranslating ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-[#10B981]" />
            ) : (
              <Languages className="w-3.5 h-3.5 text-[#10B981]" />
            )}
            <span>{isTranslating ? 'Translating to English...' : 'AI Translate to English'}</span>
          </button>
        </div>

        <textarea
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe the problem, severity, landmarks, or affected residents..."
          className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl p-3.5 text-sm text-[#102A43] placeholder-[#94A3B8] focus:outline-none focus:border-[#1E6FFF] focus:ring-1 focus:ring-[#1E6FFF] transition"
          required
        />

        {/* English Translation Preview Card */}
        {(translatedDescription || isTranslating) && (
          <div className="p-3.5 bg-[#E8F5E9]/50 border border-[#10B981]/30 rounded-2xl space-y-2 shadow-xs transition-all">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#10B981]" />
                <span className="text-[11px] font-bold text-[#102A43] uppercase tracking-wider">
                  English Translation Preview
                </span>
              </div>
              {detectedLanguage && (
                <span className="text-[10px] font-bold px-2 py-0.5 bg-[#E8F5E9] text-[#10B981] rounded-md border border-[#10B981]/30">
                  Detected: {detectedLanguage}
                </span>
              )}
            </div>
            <textarea
              rows={2}
              value={translatedDescription}
              onChange={(e) => setTranslatedDescription(e.target.value)}
              placeholder="English translation will appear here..."
              className="w-full bg-[#FFFFFF] border border-[#10B981]/40 rounded-xl p-2.5 text-xs text-[#102A43] placeholder-[#94A3B8] focus:outline-none focus:border-[#10B981] font-medium"
            />
            <p className="text-[10px] text-[#334E68] italic font-medium">
              Tip: Janseva AI uses this English translation for municipal prioritization, GIS clustering, and field crew routing.
            </p>
          </div>
        )}
      </div>

      {/* Location Picker */}
      <LocationPicker onLocationChange={handleLocationUpdate} />

      {/* Manual Ward & Address inputs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-bold text-[#102A43] mb-1">
            Ward <span className="text-[#334E68] font-normal">(e.g. Ward 14)</span>
          </label>
          <input
            type="text"
            value={ward}
            onChange={(e) => setWard(e.target.value)}
            placeholder="Ward 12, Shivaji Nagar"
            className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3.5 py-2.5 text-sm text-[#102A43] placeholder-[#94A3B8] focus:outline-none focus:border-[#1E6FFF] focus:ring-1 focus:ring-[#1E6FFF] transition"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-[#102A43] mb-1">
            Specific Landmark
          </label>
          <input
            type="text"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
            placeholder="Opposite Primary Health Center"
            className="w-full bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl px-3.5 py-2.5 text-sm text-[#102A43] placeholder-[#94A3B8] focus:outline-none focus:border-[#1E6FFF] focus:ring-1 focus:ring-[#1E6FFF] transition"
          />
        </div>
      </div>

      {/* Photo Upload */}
      <div>
        <label className="block text-xs font-bold text-[#102A43] mb-2">
          Upload Photo / Proof
        </label>
        <div className="flex items-center gap-4">
          <label className="cursor-pointer flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#F4F7FA] border border-dashed border-[#CBD5E1] hover:border-[#1E6FFF] text-xs font-bold text-[#1E6FFF] hover:bg-[#E3F2FD] transition shadow-sm">
            <Camera className="w-4 h-4 text-[#1E6FFF]" />
            <span>Select Photo / Take Picture</span>
            <input type="file" accept="image/*" capture="environment" onChange={handleFileChange} className="hidden" />
          </label>
          {mediaPreview && (
            <div className="relative group">
              <img
                src={mediaPreview}
                alt="Preview"
                className="w-12 h-12 rounded-xl object-cover border border-[#1E6FFF] shadow-sm"
              />
              <button
                type="button"
                onClick={() => setMediaPreview(null)}
                className="absolute -top-1 -right-1 bg-[#EF4444] text-[#FFFFFF] rounded-full p-0.5 text-[10px] cursor-pointer"
              >
                ✕
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={submitting}
        className="w-full py-3.5 px-6 rounded-xl font-bold text-sm tracking-wide text-[#FFFFFF] bg-[#1E6FFF] hover:bg-[#1858D6] shadow-sm flex items-center justify-center gap-2 transition-all disabled:opacity-50 cursor-pointer"
      >
        <Send className="w-4 h-4 text-[#FFFFFF]" />
        <span>{submitting ? 'Submitting & Processing with AI...' : 'Submit Grievance'}</span>
      </button>
    </form>
  );
}
