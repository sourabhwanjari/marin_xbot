"use client";

import dynamic from "next/dynamic";
import React from "react";
import { FishingZone, MarineAlert, UserLocation, HazardArea, RestrictedArea } from "@/types/marine";

const DynamicMarineMap = dynamic(() => import("./MarineMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[480px] lg:min-h-[580px] rounded-2xl border border-slate-200 bg-white flex flex-col items-center justify-center text-slate-500 space-y-3 shadow-sm">
      <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      <span className="text-xs font-semibold text-slate-700">Loading Marine GIS Engine & Bathymetry...</span>
    </div>
  ),
});

interface MapWrapperProps {
  userLocation: UserLocation;
  fishingZones: FishingZone[];
  alerts: MarineAlert[];
  hazardAreas: HazardArea[];
  restrictedAreas: RestrictedArea[];
  selectedZoneId?: string | null;
  onZoneSelect?: (zone: FishingZone) => void;
}

export const MapWrapper: React.FC<MapWrapperProps> = (props) => {
  return <DynamicMarineMap {...props} />;
};

export default MapWrapper;
