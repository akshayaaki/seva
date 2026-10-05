'use client';

import React from 'react';
import Navbar from '@/components/Navbar';
import WorkerPortal from '@/components/WorkerPortal';
import { Wrench } from 'lucide-react';

export default function WorkerPage() {
  return (
    <div className="min-h-screen bg-[#F4F7FA] text-[#102A43] flex flex-col selection:bg-[#1E6FFF] selection:text-[#FFFFFF]">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <div className="border-b border-[#E2E8F0] pb-4">
          <div className="flex items-center gap-2">
            <Wrench className="w-6 h-6 text-[#1E6FFF]" />
            <h1 className="text-2xl font-black text-[#102A43] tracking-tight">
              Field Operations & Dispatch Portal
            </h1>
          </div>
          <p className="text-xs text-[#334E68] mt-1 font-medium">
            Mobile-optimized work orders, turn-by-turn navigation, and proof-of-work submission.
          </p>
        </div>

        <WorkerPortal />
      </main>
    </div>
  );
}

