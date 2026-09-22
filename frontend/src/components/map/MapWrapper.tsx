"use client";

import dynamic from "next/dynamic";
import React from "react";
import { FishingZone, MarineAlert, UserLocation, HazardArea, RestrictedArea } from "@/types/marine";

const DynamicMarineMap = dynamic(() => import("./MarineMap"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[460px] lg:min-h-[560px] rounded-xl border border-cyan-500/20 bg-marine-950 flex flex-col items-center justify-center text-slate-400 space-y-3">
      <div className="w-8 h-8 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin"></div>
      <span className="text-sm font-medium">Loading Marine GIS Engine & Bathymetry...</span>
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
