'use client';

import React, { useState } from 'react';
import { MapPin, Navigation, Loader2, CheckCircle2, AlertTriangle } from 'lucide-react';

interface LocationPickerProps {
  onLocationChange: (loc: {
    latitude: number;
    longitude: number;
    address: string;
    ward?: string;
  }) => void;
}

export default function LocationPicker({ onLocationChange }: LocationPickerProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latitude, setLatitude] = useState<number | null>(null);
  const [longitude, setLongitude] = useState<number | null>(null);
  const [address, setAddress] = useState<string>('');
  const [accuracy, setAccuracy] = useState<number | null>(null);

  const reverseGeocode = async (lat: number, lon: number) => {
    try {
      const response = await fetch(
        `https://nominatim.openstreetmap.org/reverse?lat=${lat}&lon=${lon}&format=json`,
        {
          headers: {
            'User-Agent': 'JansevaAI-CitizenPortal/1.0',
          },
        }
      );
      if (response.ok) {
        const data = await response.json();
        const resolvedAddress = data.display_name || `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
        const wardCandidate = data.address?.suburb || data.address?.neighbourhood || data.address?.city_district;
        setAddress(resolvedAddress);
        onLocationChange({
          latitude: lat,
          longitude: lon,
          address: resolvedAddress,
          ward: wardCandidate,
        });
      } else {
        const fallback = `Coordinates: ${lat.toFixed(5)}, ${lon.toFixed(5)}`;
        setAddress(fallback);
        onLocationChange({ latitude: lat, longitude: lon, address: fallback });
      }
    } catch (e) {
      console.warn('Reverse geocoding error:', e);
      const fallback = `GPS: ${lat.toFixed(5)}, ${lon.toFixed(5)}`;
      setAddress(fallback);
      onLocationChange({ latitude: lat, longitude: lon, address: fallback });
    }
  };

  const handleDetectGPS = () => {
    setError(null);
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by your browser.');
      return;
    }

    setLoading(true);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        setLatitude(lat);
        setLongitude(lon);
        setAccuracy(Math.round(pos.coords.accuracy));
        await reverseGeocode(lat, lon);
        setLoading(false);
      },
      (err) => {
        console.error('Geo error:', err);
        setLoading(false);
        if (err.code === err.PERMISSION_DENIED) {
          setError('GPS location access was denied. Please allow location permissions.');
        } else {
          setError('Unable to retrieve GPS signal. Please enter your location manually.');
        }
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0,
      }
    );
  };

  return (
    <div className="bg-[#F4F7FA] rounded-2xl p-4 border border-[#CBD5E1] shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-[#1E6FFF]" />
          <span className="text-xs font-bold text-[#102A43] uppercase tracking-wide">
            Location Verification
          </span>
        </div>
        <button
          type="button"
          onClick={handleDetectGPS}
          disabled={loading}
          className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-[#1E6FFF] hover:bg-[#1858D6] text-[#FFFFFF] text-xs font-bold shadow-sm transition disabled:opacity-50 cursor-pointer"
        >
          {loading ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Locating GPS...</span>
            </>
          ) : (
            <>
              <Navigation className="w-3.5 h-3.5" />
              <span>Auto-Detect GPS</span>
            </>
          )}
        </button>
      </div>

      {latitude && longitude ? (
        <div className="p-3 bg-[#E8F5E9] border border-[#10B981]/30 rounded-xl text-xs space-y-1">
          <div className="flex items-center gap-1.5 text-[#10B981] font-bold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>GPS Locked ({accuracy ? `±${accuracy}m precision` : 'Accurate'})</span>
          </div>
          <p className="text-[#334E68] font-mono text-[11px]">
            {latitude.toFixed(6)}, {longitude.toFixed(6)}
          </p>
          <p className="text-[#102A43] mt-1 font-medium">{address}</p>
        </div>
      ) : (
        <div className="p-3 bg-[#FFFFFF] border border-[#CBD5E1] rounded-xl text-xs text-[#334E68]">
          Click <strong className="text-[#1E6FFF]">Auto-Detect GPS</strong> for instant location lock, or enter your ward and address manually below.
        </div>
      )}

      {error && (
        <div className="mt-2 p-2 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-xl flex items-center gap-2 text-[#EF4444] text-xs font-medium">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

