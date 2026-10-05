'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Shield, MapPin, Wrench, BarChart3, Bell, PhoneCall } from 'lucide-react';

export default function Navbar() {
  const pathname = usePathname();

  const navLinks = [
    { href: '/', label: 'Citizen Grievance', icon: MapPin },
    { href: '/command', label: 'Command Center', icon: Shield },
    { href: '/worker', label: 'Field Operations', icon: Wrench },
    { href: '/admin', label: 'Municipal Admin', icon: BarChart3 },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#FFFFFF]/95 backdrop-blur border-b border-[#E2E8F0] text-[#102A43] shadow-sm">
      {/* Civic Emergency Helpline Ribbon */}
      <div className="bg-[#1E6FFF] px-4 py-1.5 text-xs font-semibold flex items-center justify-between text-[#FFFFFF]">
        <div className="flex items-center gap-2">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-[#10B981] animate-pulse" />
          <span>MUNICIPAL HELPLINE 24x7: <strong className="font-bold tracking-wide">1800-JANSEVA (1800-526-7382)</strong></span>
        </div>
        <div className="flex items-center gap-4">
          <span className="hidden sm:inline text-[#E3F2FD]">Rapid Response & Triage Active</span>
          <span className="bg-[#FFFFFF]/20 text-[#FFFFFF] px-2 py-0.5 rounded text-[10px] tracking-wider uppercase font-bold border border-white/30">
            Official Civic Portal
          </span>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Identity */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-[#1E6FFF] flex items-center justify-center shadow-md group-hover:scale-105 transition-transform text-[#FFFFFF]">
              <Shield className="w-5 h-5 font-bold" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-xl tracking-tight text-[#102A43]">
                  Janseva AI
                </span>
                <span className="text-[11px] px-1.5 py-0.5 bg-[#E8F5E9] text-[#10B981] font-bold rounded border border-[#10B981]/30">
                  Civic AI
                </span>
              </div>
              <p className="text-xs text-[#334E68] -mt-0.5 font-medium">From citizen voice to civic action</p>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1.5">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-bold transition-all ${
                    isActive
                      ? 'bg-[#1E6FFF] text-[#FFFFFF] shadow-sm'
                      : 'text-[#334E68] hover:text-[#102A43] hover:bg-[#F4F7FA]'
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? 'text-[#FFFFFF]' : 'text-[#1E6FFF]'}`} />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right Status & Actions */}
          <div className="flex items-center gap-3">
            <button
              title="System Notifications"
              className="p-2 rounded-xl text-[#334E68] hover:text-[#102A43] hover:bg-[#F4F7FA] transition relative"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#EF4444] animate-ping" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-[#EF4444]" />
            </button>

            <a
              href="tel:18005267382"
              className="hidden lg:flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-[#E3F2FD] text-[#1E6FFF] text-xs font-bold hover:bg-[#1E6FFF] hover:text-[#FFFFFF] border border-[#1E6FFF]/30 transition shadow-sm"
            >
              <PhoneCall className="w-3.5 h-3.5 text-[#1E6FFF] group-hover:text-[#FFFFFF]" />
              <span>SOS Call</span>
            </a>
          </div>
        </div>
      </div>
    </header>
  );
}

