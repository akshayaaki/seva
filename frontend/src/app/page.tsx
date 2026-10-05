'use client';

import React, { useState } from 'react';
import Navbar from '@/components/Navbar';
import GrievanceForm from '@/components/GrievanceForm';
import ComplaintTracker from '@/components/ComplaintTracker';
import {
  Clock,
  Sparkles,
  Compass,
  Building2,
  FileCheck2,
} from 'lucide-react';
import { Complaint } from '@/types';

export default function CitizenPortal() {
  const [activeTab, setActiveTab] = useState<'submit' | 'track'>('submit');

  const handleSubmissionSuccess = (complaint: Complaint) => {
    // Keep user updated
  };

  return (
    <div className="min-h-screen bg-[#F4F7FA] text-[#102A43] flex flex-col selection:bg-[#1E6FFF] selection:text-[#FFFFFF]">
      <Navbar />

      {/* Hero Section with Cityscape Municipal Banner */}
      <section className="relative overflow-hidden border-b border-[#E2E8F0] bg-cover bg-center py-14 sm:py-18 px-4 sm:px-6 lg:px-8 shadow-sm" style={{ backgroundImage: "url('/hero-banner.jpg')" }}>
        {/* Soft Glassmorphic Gradient Overlay for Contrast & Readability */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#FFFFFF]/85 via-[#FFFFFF]/80 to-[#F4F7FA]/95 backdrop-blur-[1.5px]" />

        <div className="max-w-5xl mx-auto text-center relative z-10 space-y-4">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#E8F5E9] border border-[#10B981]/30 text-[#10B981] text-xs font-bold uppercase tracking-wider shadow-sm">
            <Sparkles className="w-3.5 h-3.5 text-[#10B981]" />
            <span>AI-Driven Municipal Service Assurance</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-black tracking-tight text-[#102A43] leading-tight">
            Janseva AI Grievance Portal
            <span className="block text-xl sm:text-2xl font-semibold text-[#1E6FFF] mt-2">
              Citizen Redressal & Field Operations Platform
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-[#334E68] text-sm sm:text-base leading-relaxed font-medium">
            Submit municipal complaints via voice, text, or photos with automatic English translation.
            Our automated AI engine geocodes, clusters duplicates, and dispatches field teams with strict SLA enforcement.
          </p>

          {/* Quick Metrics */}
          <div className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-3.5 max-w-3xl mx-auto text-left">
            <div className="bg-[#FFFFFF]/95 backdrop-blur-md border border-[#E2E8F0] p-4 rounded-2xl shadow-sm hover:shadow-md transition-all">
              <span className="text-xs text-[#334E68] font-semibold flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-[#1E6FFF]" /> SLA Response
              </span>
              <span className="text-xl font-black text-[#102A43] mt-1 block">&lt; 4 Hours</span>
            </div>

            <div className="bg-[#FFFFFF]/95 backdrop-blur-md border border-[#E2E8F0] p-4 rounded-2xl shadow-sm hover:shadow-md transition-all">
              <span className="text-xs text-[#334E68] font-semibold flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-[#10B981]" /> Geolocation
              </span>
              <span className="text-xl font-black text-[#102A43] mt-1 block">GPS Precise</span>
            </div>

            <div className="bg-[#FFFFFF]/95 backdrop-blur-md border border-[#E2E8F0] p-4 rounded-2xl shadow-sm hover:shadow-md transition-all">
              <span className="text-xs text-[#334E68] font-semibold flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#1E6FFF]" /> AI Triage
              </span>
              <span className="text-xl font-black text-[#102A43] mt-1 block">Multi-Language</span>
            </div>

            <div className="bg-[#FFFFFF]/95 backdrop-blur-md border border-[#E2E8F0] p-4 rounded-2xl shadow-sm hover:shadow-md transition-all">
              <span className="text-xs text-[#334E68] font-semibold flex items-center gap-1.5">
                <FileCheck2 className="w-3.5 h-3.5 text-[#10B981]" /> Verification
              </span>
              <span className="text-xl font-black text-[#102A43] mt-1 block">Photo Proof</span>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main className="flex-1 max-w-4xl w-full mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Toggle Tabs */}
        <div className="flex bg-[#FFFFFF] p-1.5 rounded-2xl border border-[#E2E8F0] max-w-md mx-auto shadow-sm">
          <button
            onClick={() => setActiveTab('submit')}
            className={`flex-1 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'submit'
                ? 'bg-[#1E6FFF] text-[#FFFFFF] shadow-sm'
                : 'text-[#334E68] hover:text-[#102A43] hover:bg-[#F4F7FA]'
            }`}
          >
            File New Grievance
          </button>
          <button
            onClick={() => setActiveTab('track')}
            className={`flex-1 py-2.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'track'
                ? 'bg-[#1E6FFF] text-[#FFFFFF] shadow-sm'
                : 'text-[#334E68] hover:text-[#102A43] hover:bg-[#F4F7FA]'
            }`}
          >
            Track Grievance Status
          </button>
        </div>

        {/* Tab Components */}
        {activeTab === 'submit' ? (
          <GrievanceForm onSuccess={handleSubmissionSuccess} />
        ) : (
          <ComplaintTracker />
        )}
      </main>

      {/* Civic Footer */}
      <footer className="border-t border-[#E2E8F0] bg-[#FFFFFF] py-8 px-4 text-center text-xs text-[#334E68]">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-[#1E6FFF]" />
            <span className="font-bold text-[#102A43]">Janseva AI Municipal Grievance Redressal</span>
          </div>
          <div>
            <span>Official Urban Local Body Digital Infrastructure • Powered by Gemini & PostGIS</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
