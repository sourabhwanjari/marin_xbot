import { MarineConditions, FishingZone, MarineAlert, ChatMessage, RagStatus, SourceCitation, ExecutionStep, AgentChatRequest, AgentChatResponse, DataSourcesHealthResponse } from "@/types/marine";
import { marineConditions } from "@/data/marineData";
import { mockFishingZones } from "@/data/fishingZones";
import { mockAlerts } from "@/data/alerts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchHealth(): Promise<{ status: string; service: string; is_demo: boolean }> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend /health unreachable, using local fallback status:", err);
    return { status: "ok", service: "MARINEX AI (Local Fallback)", is_demo: true };
  }
}

export async function fetchMarineConditions(): Promise<MarineConditions> {
  try {
    const res = await fetch(`${API_BASE_URL}/marine/conditions`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend /marine/conditions unreachable, using local mock data:", err);
    return marineConditions;
  }
}

export async function fetchFishingZones(): Promise<FishingZone[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/marine/fishing-zones`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend /marine/fishing-zones unreachable, using local mock data:", err);
    return mockFishingZones;
  }
}

export async function fetchMarineAlerts(): Promise<MarineAlert[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/marine/alerts`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend /marine/alerts unreachable, using local mock data:", err);
    return mockAlerts;
  }
}

export async function fetchRagStatus(): Promise<RagStatus> {
  try {
    const res = await fetch(`${API_BASE_URL}/rag/status`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend /rag/status unreachable, using fallback RAG status:", err);
    return {
      status: "ready",
      total_documents: 2,
      total_chunks: 8,
      embedding_provider: "deterministic-local",
      storage_path: "./storage/chroma",
      documents: [
        { file_name: "demo_marine_safety.txt", doc_type: "txt", total_chunks: 4, date_added: "2026-09-22 03:00" },
        { file_name: "demo_fishing_guidelines.txt", doc_type: "txt", total_chunks: 4, date_added: "2026-09-22 03:00" },
      ],
      is_available: true,
    };
  }
}

export async function fetchDataSourcesStatus(): Promise<DataSourcesHealthResponse> {
  try {
    const res = await fetch(`${API_BASE_URL}/data-sources/status`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend /data-sources/status unreachable, using fallback status:", err);
    return {
      weather: { enabled: true, status: "online", provider: "Open-Meteo Weather (Local Fallback)", is_live: false },
      ocean: { enabled: true, status: "online", provider: "Open-Meteo Marine / INCOIS (Local Fallback)", is_live: false },
      pfz: { enabled: true, status: "online", provider: "INCOIS PFZ (Local Fallback)", is_live: true },
      satellite: { enabled: false, status: "not_configured", provider: "ISRO MOSDAC" },
      postgis: { enabled: false, status: "not_configured", provider: "PostgreSQL / PostGIS" },
      gis: { enabled: true, status: "online", provider: "GeoJSON Spatial Engine" },
      demo_mode: true,
      overall_status: "operational"
    };
  }
}

export async function fetchPfzGeoJson(location?: string): Promise<any> {
  try {
    const url = location ? `${API_BASE_URL}/data-sources/pfz?location=${encodeURIComponent(location)}` : `${API_BASE_URL}/data-sources/pfz`;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend /data-sources/pfz unreachable:", err);
    return null;
  }
}

export async function fetchGeospatialLayers(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE_URL}/data-sources/geospatial`, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn("Backend /data-sources/geospatial unreachable:", err);
    return null;
  }
}

export async function triggerIngestion(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/rag/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) throw new Error(`Ingestion failed with status ${res.status}`);
  return await res.json();
}

export async function uploadDocument(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/rag/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || `Upload failed with status ${res.status}`);
  }
  return await res.json();
}

export interface ChatApiResponse {
  message: string;
  source: string;
  is_demo: boolean;
  suggested_actions?: string[];
  related_zones?: string[];
  sources?: SourceCitation[];
  is_rag?: boolean;
  retrieved_chunks?: number;
  risk_level?: string;
  evidence?: string[];
  execution_steps?: ExecutionStep[];
  location?: string;
  time_context?: string;
}

export async function sendAgentChatMessage(request: AgentChatRequest): Promise<AgentChatResponse> {
  const res = await fetch(`${API_BASE_URL}/agent/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) throw new Error(`Agent chat failed with HTTP ${res.status}`);
  return await res.json();
}

export async function sendChatMessage(message: string, location?: string): Promise<ChatApiResponse> {
  try {
    // Attempt dedicated LangGraph multi-agent endpoint first
    const agentRes = await fetch(`${API_BASE_URL}/agent/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, location }),
    });

    if (agentRes.ok) {
      const data: AgentChatResponse = await agentRes.json();
      let suggestedActions = ["Check Current Sea State", "View Active Alerts"];
      if (data.risk_level === "MEDIUM" || data.risk_level === "HIGH") {
        suggestedActions = ["Inspect Swell on Map", "View Port Control Notices", "Check Safety Guidelines"];
      } else if (data.intent === "pfz_discovery") {
        suggestedActions = ["Show Zone Alpha on Map", "Check Weather along Route"];
      }

      return {
        message: data.answer,
        source: `langgraph-multi-agent (${data.data_status})`,
        is_demo: data.is_demo,
        suggested_actions: suggestedActions,
        related_zones: data.location ? [`${data.location} Sector`] : [],
        sources: data.sources || [],
        is_rag: (data.sources && data.sources.length > 0) || false,
        retrieved_chunks: data.sources ? data.sources.length : 0,
        risk_level: data.risk_level,
        evidence: data.evidence || [],
        execution_steps: data.execution_steps || [],
        location: data.location,
        time_context: data.time_context,
      };
    }

    // Fallback to /chat endpoint
    const chatRes = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (!chatRes.ok) throw new Error(`HTTP error ${chatRes.status}`);
    return await chatRes.json();
  } catch (err) {
    console.warn("Backend /agent/chat and /chat unreachable, synthesizing local mock response:", err);

    const msg = message.toLowerCase();
    if (msg.includes("safe") || msg.includes("fishing") && (msg.includes("tomorrow") || msg.includes("mumbai"))) {
      return {
        message: "SAFETY ASSESSMENT: CAUTION ADVISED (DEMO)\n\n" +
          "Key Conditions near Mumbai:\n" +
          "• Wave Height: 2.3m (Caution threshold: 2.0m for small craft)\n" +
          "• Wind: 18.0 knots (Gusts up to 24 knots)\n" +
          "• Sea State: Moderate with active southwesterly swell\n\n" +
          "Recommendation:\n" +
          "Small artisanal craft (<9m) should defer offshore trips or remain within sheltered waters. " +
          "Mechanized vessels (>15m) may operate with heightened vigilance and continuous VHF Channel 16 watch.",
        source: "langgraph-multi-agent (local fallback demo)",
        is_demo: true,
        risk_level: "MEDIUM",
        location: "Mumbai",
        time_context: "tomorrow morning",
        evidence: [
          "Significant wave height: 2.3m (Threshold for small craft: 2.0m)",
          "Wind speed: 18.0 knots (Gusts up to 24.0 knots)",
          "Rain probability: 45%",
          "Nearest port: Mumbai Port Trust (7.5 km)"
        ],
        execution_steps: [
          { agent: "planner", status: "completed", details: "Classified fishing_safety near Mumbai" },
          { agent: "weather", status: "completed", details: "Retrieved wind (18kt) and rain probability (45%)" },
          { agent: "ocean", status: "completed", details: "Retrieved wave height (2.3m) and SST (28.2°C)" },
          { agent: "geospatial", status: "completed", details: "Validated Mumbai coastal sector" },
          { agent: "risk", status: "completed", details: "Determined MEDIUM risk level" },
          { agent: "response", status: "completed", details: "Synthesized marine decision recommendation" }
        ],
        suggested_actions: ["Inspect Swell on Map", "View Port Control Notices", "Check Safety Guidelines"],
        related_zones: ["Mumbai Sector"],
        sources: [
          { file: "demo_marine_safety.txt", page: 1, doc_type: "txt" }
        ],
        is_rag: true,
        retrieved_chunks: 1
      };
    } else if (msg.includes("guideline") || msg.includes("safety") || msg.includes("wave") && msg.includes("say")) {
      return {
        message: "According to the Marine Safety and Heavy Weather Standard Operating Guidelines (DEMO):\n\n• When significant wave heights exceed 2.0 meters, small artisanal craft (canoes and catamarans under 9m) must cease offshore transit and remain in sheltered lagoons.\n• Mechanized vessels (>15m LOA) may operate up to 25 NM offshore with continuous VHF Channel 16 watch.\n• When wave heights exceed 3.5 meters (Rough to Very Rough), all operations are suspended.",
        source: "rag-knowledge-base (local fallback)",
        is_demo: true,
        suggested_actions: ["Check Current Sea State", "View Active Alerts"],
        sources: [
          { file: "demo_marine_safety.txt", page: 1, doc_type: "txt" }
        ],
        is_rag: true,
        retrieved_chunks: 2
      };
    } else if (msg.includes("nearest") || msg.includes("fishing zone") || msg.includes("pfz") || msg.includes("fish")) {
      return {
        message: "Based on the currently available marine data, the nearest favorable fishing zone is approximately 24 km from your selected location (Zone Alpha - Chennai Offshore).\n\n• Sea Surface Temperature: 28.4°C\n• Chlorophyll: High (Thermal gradient detected)\n• Sea condition: Moderate (Wave height: 1.8m)\n• Estimated fishing suitability: Favorable 🟢\n• Target pelagic species: Sardine, Mackerel, Tuna\n\nView the location on the map for more details.",
        source: "langgraph-multi-agent (local fallback)",
        is_demo: true,
        suggested_actions: ["Show Zone Alpha on Map", "Check Weather along Route"],
        related_zones: ["Zone Alpha - Chennai Offshore"],
        sources: [],
        is_rag: false,
        retrieved_chunks: 0
      };
    } else {
      return {
        message: `Marine Intelligence Query Received: "${message}"\n\nI can synthesize information regarding:\n• Fishing trip safety assessments (orchestrating Weather, Ocean, Geospatial & Risk agents)\n• Marine safety guidelines and fishing regulations (via RAG Knowledge Base)\n• Potential Fishing Zones (PFZs) derived from SST & Chlorophyll fronts\n• Oceanographic conditions (Wave height, Sea state, Currents, Water temp)\n\nTry asking: 'Is it safe to go fishing tomorrow morning near Mumbai?' or 'Where is the nearest Potential Fishing Zone?'`,
        source: "langgraph-multi-agent (local fallback)",
        is_demo: true,
        suggested_actions: ["Is it safe to go fishing tomorrow morning near Mumbai?", "Find Nearest PFZ"],
        sources: [],
        is_rag: false,
        retrieved_chunks: 0
      };
    }
  }
}
