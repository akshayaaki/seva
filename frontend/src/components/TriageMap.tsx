'use client';

import React, { useEffect, useRef } from 'react';
import 'leaflet/dist/leaflet.css';
import { Incident } from '@/types';

interface TriageMapProps {
  incidents: Incident[];
  selectedIncident?: Incident | null;
  onSelectIncident: (inc: Incident) => void;
}

export default function TriageMap({
  incidents,
  selectedIncident,
  onSelectIncident,
}: TriageMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);

  useEffect(() => {
    if (typeof window === 'undefined' || !mapContainerRef.current) return;

    let L: any;
    let isMounted = true;

    import('leaflet').then((leafletModule) => {
      if (!isMounted || !mapContainerRef.current) return;
      L = leafletModule.default || leafletModule;

      delete (L.Icon.Default.prototype as any)._getIconUrl;
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      });

      if (!mapInstanceRef.current) {
        const centerLat = incidents.length > 0 ? incidents[0].latitude : 19.0760;
        const centerLon = incidents.length > 0 ? incidents[0].longitude : 72.8777;

        const map = L.map(mapContainerRef.current).setView([centerLat, centerLon], 12);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors | Janseva AI GIS',
          maxZoom: 19,
        }).addTo(map);

        mapInstanceRef.current = map;

        setTimeout(() => {
          if (mapInstanceRef.current) {
            mapInstanceRef.current.invalidateSize();
          }
        }, 150);
      } else {
        mapInstanceRef.current.invalidateSize();
      }

      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];

      const map = mapInstanceRef.current;

      const getMarkerColor = (level: string) => {
        switch (level) {
          case 'CRITICAL':
            return '#EF4444'; // Alert Red
          case 'HIGH':
            return '#F59E0B'; // Warm Orange
          case 'MEDIUM':
            return '#1E6FFF'; // Primary Blue
          case 'LOW':
            return '#10B981'; // Accent Green
          default:
            return '#334E68';
        }
      };

      incidents.forEach((inc) => {
        const color = getMarkerColor(inc.priority_level);
        const markerHtml = `
          <div style="
            background-color: ${color};
            width: 26px;
            height: 26px;
            border-radius: 50%;
            border: 2px solid #ffffff;
            box-shadow: 0 2px 6px rgba(0,0,0,0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            color: #ffffff;
            font-size: 11px;
            font-weight: 800;
          ">
            ${inc.complaint_count || 1}
          </div>
        `;

        const customIcon = L.divIcon({
          html: markerHtml,
          className: 'custom-leaflet-marker',
          iconSize: [26, 26],
          iconAnchor: [13, 13],
        });

        const marker = L.marker([inc.latitude, inc.longitude], { icon: customIcon })
          .addTo(map)
          .bindPopup(`
            <div style="font-family: sans-serif; font-size: 12px; color: #102A43; line-height: 1.4;">
              <strong style="color: ${color};">${inc.priority_level}</strong>: ${inc.title}<br/>
              <strong>Status:</strong> ${inc.status}<br/>
              <strong>Cluster Count:</strong> ${inc.complaint_count} reports<br/>
              <small style="color: #334E68;">${inc.address || ''}</small>
            </div>
          `);

        marker.on('click', () => {
          onSelectIncident(inc);
        });

        markersRef.current.push(marker);
      });

      if (
        selectedIncident &&
        selectedIncident.latitude != null &&
        selectedIncident.longitude != null &&
        !isNaN(Number(selectedIncident.latitude)) &&
        !isNaN(Number(selectedIncident.longitude))
      ) {
        map.flyTo([Number(selectedIncident.latitude), Number(selectedIncident.longitude)], 15, {
          duration: 1.2,
        });
      }
    });

    return () => {
      isMounted = false;
    };
  }, [incidents, selectedIncident, onSelectIncident]);

  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  return (
    <div className="relative w-full h-[520px] rounded-3xl overflow-hidden border border-[#E2E8F0] shadow-sm bg-[#FFFFFF]">
      <div ref={mapContainerRef} className="w-full h-full z-10" />

      {/* Map Legend */}
      <div className="absolute top-4 right-4 z-20 bg-[#FFFFFF]/95 backdrop-blur border border-[#E2E8F0] px-3.5 py-2.5 rounded-2xl text-xs space-y-1.5 shadow-md text-[#102A43]">
        <span className="font-bold text-[10px] uppercase tracking-wider text-[#334E68] block mb-1">
          Priority GIS Clusters
        </span>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#EF4444]" />
          <span className="font-medium">Critical Severity</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#F59E0B]" />
          <span className="font-medium">High Urgency</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#1E6FFF]" />
          <span className="font-medium">Medium Priority</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#10B981]" />
          <span className="font-medium">Low Priority</span>
        </div>
      </div>
    </div>
  );
}

