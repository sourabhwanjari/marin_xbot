export type AlertSeverity = 'LOW' | 'MEDIUM' | 'HIGH';

export interface MarineConditions {
  seaSurfaceTemperature: number;
  chlorophyll: string;
  waveHeight: number;
  windSpeed: number;
  windDirection?: string;
  seaState: string;
  visibility: number;
  airTemperature?: number;
  tide?: string;
  updatedAt?: string;
}

export interface FishingZone {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  distanceKm: number;
  seaSurfaceTemperature: number;
  chlorophyll: string;
  suitability: 'Favorable' | 'Moderate' | 'Unfavorable';
  status: 'Favorable' | 'Caution' | 'Hazard';
  dominantSpecies?: string[];
  depthMeters?: number;
}

export interface MarineAlert {
  id: string;
  type: string;
  severity: AlertSeverity;
  location: string;
  latitude: number;
  longitude: number;
  radius_km: number;
  time: string;
  short_description: string;
  advisory?: string;
}

export interface UserLocation {
  name: string;
  latitude: number;
  longitude: number;
  portName: string;
}

export interface HazardArea {
  id: string;
  name: string;
  type: 'High Wave' | 'Storm' | 'Rough Sea';
  coordinates: [number, number][]; // Polygon coordinates [[lat, lon], ...]
  severity: AlertSeverity;
  description: string;
}

export interface RestrictedArea {
  id: string;
  name: string;
  type: 'Naval Channel' | 'Marine Sanctuary' | 'Port Security' | 'International Boundary';
  coordinates: [number, number][];
  description: string;
}

export interface SourceCitation {
  file: string;
  page: number;
  doc_type?: string;
  chunk_id?: string;
}

export interface ExecutionStep {
  agent: string;
  status: string;
  details?: string;
}

export interface MarineRouteConditions {
  avg_wind_speed_knots?: number;
  max_wave_height_m?: number;
  sea_surface_temp_c?: number;
  sea_state?: string;
  weather_summary?: string;
  tide_status?: string;
  advisory_active?: boolean;
  squall_warning?: string;
}

export interface RoutePoint {
  latitude: number;
  longitude: number;
  name?: string;
  port?: string;
}

export interface MarineRoute {
  route_id: string;
  origin: RoutePoint;
  destination: RoutePoint;
  distance_km: number;
  estimated_duration_hours: number;
  estimated_duration_text: string;
  safety_score: number;
  risk_level: 'LOW' | 'MODERATE' | 'HIGH' | 'UNAVAILABLE' | string;
  waypoints: [number, number][]; // [[lat, lon], ...]
  route_geometry?: {
    type: string;
    coordinates: [number, number][];
  };
  route_conditions?: MarineRouteConditions;
  warnings?: string[];
  hazards_avoided?: string[];
  avoided_zones?: string[];
  explanation?: string;
  status?: string;
  alternative_routes?: any[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  isDemo?: boolean;
  source?: string;
  suggestedActions?: string[];
  relatedZones?: string[];
  sources?: SourceCitation[];
  isRag?: boolean;
  retrievedChunks?: number;
  riskLevel?: 'LOW' | 'MEDIUM' | 'HIGH' | string;
  evidence?: string[];
  executionSteps?: ExecutionStep[];
  location?: string;
  timeContext?: string;
  route?: MarineRoute;
  detected_language?: string;
  response_language?: string;
  map_data?: Record<string, any>;
}

export interface ChatHistoryItem {
  role: 'user' | 'assistant';
  content: string;
}

export interface AgentChatRequest {
  message: string;
  location?: string;
  history?: ChatHistoryItem[];
}

export interface AgentChatResponse {
  answer: string;
  intent: string;
  risk_level?: string;
  location?: string;
  time_context?: string;
  sources?: SourceCitation[];
  evidence?: string[];
  weather?: Record<string, any>;
  ocean?: Record<string, any>;
  geospatial?: Record<string, any>;
  risk?: Record<string, any>;
  route?: MarineRoute;
  detected_language?: string;
  response_language?: string;
  map_data?: Record<string, any>;
  execution_steps?: ExecutionStep[];
  data_status: string;
  is_demo: boolean;
}


export interface RagDocumentInfo {
  file_name: string;
  doc_type: string;
  total_chunks: number;
  date_added?: string;
}

export interface RagStatus {
  status: string;
  total_documents: number;
  total_chunks: number;
  embedding_provider: string;
  storage_path: string;
  documents: RagDocumentInfo[];
  is_available: boolean;
}

export interface DataSourceItemStatus {
  enabled: boolean;
  status: string;
  provider?: string;
  is_live?: boolean;
  message?: string;
}

export interface DataSourcesHealthResponse {
  weather: DataSourceItemStatus;
  ocean: DataSourceItemStatus;
  pfz: DataSourceItemStatus;
  satellite: DataSourceItemStatus;
  postgis: DataSourceItemStatus;
  gis: DataSourceItemStatus;
  demo_mode: boolean;
  overall_status: string;
}

