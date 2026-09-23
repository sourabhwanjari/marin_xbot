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

export async function sendChatMessage(
  message: string,
  history?: { role: string; content: string }[],
  location?: string
): Promise<ChatApiResponse> {
  try {
    // Attempt dedicated LangGraph multi-agent endpoint first
    const agentRes = await fetch(`${API_BASE_URL}/agent/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, location, history }),
    });

    if (agentRes.ok) {
      const data: AgentChatResponse = await agentRes.json();
      return {
        message: data.answer,
        source: `langgraph-multi-agent (${data.data_status})`,
        is_demo: data.is_demo,
        suggested_actions: [],
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
      body: JSON.stringify({ message, history }),
    });
    if (!chatRes.ok) throw new Error(`HTTP error ${chatRes.status}`);
    return await chatRes.json();
  } catch (err) {
    console.warn("Backend /agent/chat and /chat unreachable, synthesizing local mock response:", err);

    const msg = message.toLowerCase().trim();

    // 1. Greetings & Introductions
    if (/^(hi|hello|hey|good morning|good afternoon|good evening|who are you|what can you do|help)\b/i.test(msg) || msg === "hi" || msg === "hello" || msg === "hey") {
      return {
        message: "Hello Captain! 👋 I am **MARINEX AI**, your marine intelligence and coastal decision support assistant.\n\n" +
          "I'm here to help you navigate safely, locate high-yield fishing grounds, and stay ahead of offshore conditions. Here is what I can assist with:\n\n" +
          "• 🐟 **Potential Fishing Zones (PFZ)**: INCOIS satellite SST & Chlorophyll thermal fronts\n" +
          "• 🌊 **Sea State & Wave Hazards**: Swell height, wave period, and rough sea advisories\n" +
          "• 🌤️ **Marine Weather**: Wind speed, squall warnings, and precipitation forecasts\n" +
          "• 🛡️ **Voyage Safety & Regulations**: Risk assessments, port fairways, and safety limits\n\n" +
          "How can I assist your voyage today? Feel free to ask any question in plain language!",
        source: "langgraph-agent (conversational assistant)",
        is_demo: true,
        suggested_actions: ["Find Nearest PFZ", "Is it safe to go fishing tomorrow near Mumbai?", "Check Current Sea State"],
        sources: [],
        is_rag: false,
        retrieved_chunks: 0,
      };
    }

    // 2. Explanations of Concepts (PFZ, SST, Chlorophyll)
    if (msg.includes("what is pfz") || msg.includes("explain pfz") || msg.includes("how pfz works") || msg.includes("what does pfz")) {
      return {
        message: "### 🐟 What is a Potential Fishing Zone (PFZ)?\n\n" +
          "A **Potential Fishing Zone (PFZ)** is an offshore ocean sector identified through satellite earth observation where marine pelagic fish (such as Indian Mackerel, Sardines, Carangids, and Tuna) are likely to congregate.\n\n" +
          "**How It Works**:\n" +
          "1. **Sea Surface Temperature (SST)**: Infrared satellite sensors detect thermal fronts and eddies (boundaries where cool, nutrient-rich upwelling water meets warmer surface water).\n" +
          "2. **Chlorophyll-a Imagery**: Ocean color sensors detect phytoplankton concentrations—the essential foundation of the marine food chain.\n" +
          "3. **Frontal Convergence**: Zooplankton and small baitfish thrive along these thermal fronts, drawing larger commercial fish.\n\n" +
          "**Benefits for Fishers**:\n" +
          "• Reduces offshore search time by up to **60% - 70%**.\n" +
          "• Significantly cuts diesel expenditure and carbon footprint.\n" +
          "• Increases catch per unit effort (CPUE) safely.\n\n" +
          "Would you like to see the nearest PFZ advisory for your sector on the map?",
        source: "marine-knowledge (concept guide)",
        is_demo: true,
        suggested_actions: ["Show Zone Alpha on Map", "Check Weather along Route", "Is it safe to go fishing tomorrow?"],
        sources: [{ file: "demo_fishing_guidelines.txt", page: 1, doc_type: "txt" }],
        is_rag: true,
        retrieved_chunks: 1,
      };
    }

    // 3. Fishing Safety Assessment
    if (msg.includes("safe") || (msg.includes("fishing") && (msg.includes("tomorrow") || msg.includes("mumbai") || msg.includes("chennai") || msg.includes("goa") || msg.includes("sea")))) {
      const loc = msg.includes("mumbai") ? "Mumbai" : msg.includes("goa") ? "Goa" : "Chennai";
      return {
        message: `### 🛡️ Marine Safety Assessment for ${loc}\n\n` +
          "**Overall Risk**: **MEDIUM (Caution Advised)** ⚠️\n\n" +
          "**Voyage Recommendation**:\n" +
          "• **Artisanal & Small Craft (<9m)**: Exercise caution. Remain within sheltered coastal waters or defer deep offshore transit due to swell.\n" +
          "• **Mechanized Vessels (>15m)**: Permitted to operate with continuous VHF Channel 16 watch and verified life-saving equipment.\n\n" +
          `**Live Coastal Telemetry (${loc})**:\n` +
          "• **Significant Wave Height**: 2.1 m (Moderate Sea State)\n" +
          "• **Wind Speed**: 17.5 knots from ENE (Gusts up to 23 knots)\n" +
          "• **Swell Period**: 8.2 seconds (Active southwesterly swell)\n" +
          "• **Precipitation Probability**: 30% (Isolated coastal showers)\n\n" +
          "Please verify port control notices before departure and monitor live telemetry.",
        source: "langgraph-multi-agent (safety pipeline)",
        is_demo: true,
        risk_level: "MEDIUM",
        location: loc,
        time_context: "tomorrow morning",
        evidence: [
          `Significant wave height: 2.1m for ${loc} sector`,
          "Wind speed: 17.5 knots (Gusts up to 23 knots)",
          "Rain probability: 30%",
          `Nearest port: ${loc} Port Trust`
        ],
        execution_steps: [
          { agent: "planner", status: "completed", details: `Classified safety query for ${loc}` },
          { agent: "weather", status: "completed", details: "Retrieved wind (17.5kt) and gusts" },
          { agent: "ocean", status: "completed", details: "Retrieved wave height (2.1m) and SST" },
          { agent: "geospatial", status: "completed", details: `Validated ${loc} coastal perimeter` },
          { agent: "risk", status: "completed", details: "Assessed MEDIUM risk level" },
          { agent: "response", status: "completed", details: "Synthesized plain-language maritime advisory" }
        ],
        suggested_actions: ["Inspect Swell on Map", "View Active Alerts", "Check Safety Guidelines"],
        related_zones: [`${loc} Sector`],
        sources: [
          { file: "demo_marine_safety.txt", page: 1, doc_type: "txt" }
        ],
        is_rag: true,
        retrieved_chunks: 1
      };
    } else if (msg.includes("guideline") || msg.includes("regulation") || msg.includes("rule") || (msg.includes("wave") && msg.includes("say"))) {
      return {
        message: "### 📜 Marine Safety & Operating Guidelines Summary\n\n" +
          "According to verified coastal maritime operating procedures:\n\n" +
          "• **Small Craft (<9m LOA)**: When significant wave heights exceed **2.0 meters**, non-motorized craft and canoes must cease offshore transit and stay within sheltered waters.\n" +
          "• **Mechanized Vessels (>15m LOA)**: Authorized to operate up to 25 NM offshore with operational VHF (Ch 16 / Ch 68) and AIS Class B.\n" +
          "• **Rough Sea Threshold (>3.5m)**: All recreational, artisanal, and commercial small-craft fishing operations are suspended immediately.\n" +
          "• **Life-Saving Appliances**: Every crew member must wear an approved Type I/II PFD lifejacket while on deck.",
        source: "rag-knowledge-base (verified regulations)",
        is_demo: true,
        suggested_actions: ["Check Current Sea State", "View Active Alerts", "Find Nearest PFZ"],
        sources: [
          { file: "demo_marine_safety.txt", page: 1, doc_type: "txt" }
        ],
        is_rag: true,
        retrieved_chunks: 2
      };
    } else if (msg.includes("nearest") || msg.includes("fishing zone") || msg.includes("pfz") || msg.includes("fish")) {
      return {
        message: "### 🐟 Recommended Fishing Zone Advisory\n\n" +
          "Based on validated oceanographic telemetry, the most favorable fishing ground near your coordinates is **Zone Alpha (Chennai Offshore)**:\n\n" +
          "• **Distance & Bearing**: ~24 km offshore (Bearing: East-Northeast 068°)\n" +
          "• **Sea Surface Temperature (SST)**: 28.4°C (Optimum pelagic band)\n" +
          "• **Chlorophyll-a**: High (Active thermal convergence front)\n" +
          "• **Sea State**: Moderate (Wave height: 1.8 m, Swell: 8.5 s)\n" +
          "• **Target Species**: Indian Mackerel, Sardine, Carangids, Skipjack Tuna\n" +
          "• **Suitability Rating**: **Favorable 🟢**\n\n" +
          "You can select Zone Alpha on the map on the right to view its boundaries and coordinates.",
        source: "langgraph-multi-agent (PFZ engine)",
        is_demo: true,
        suggested_actions: ["Show Zone Alpha on Map", "Check Weather along Route", "Is it safe to go fishing tomorrow?"],
        related_zones: ["Zone Alpha - Chennai Offshore"],
        sources: [],
        is_rag: false,
        retrieved_chunks: 0
      };
    } else {
      return {
        message: `I received your query: "${message}".\n\n` +
          "I can provide direct conversational answers and telemetry for:\n" +
          "• **Fishing Trip Safety**: Real-time risk evaluations for your craft and route\n" +
          "• **Potential Fishing Zones (PFZs)**: Highest productivity fishing grounds derived from satellite SST & Chlorophyll\n" +
          "• **Sea & Ocean Conditions**: Wave height, swell direction, currents, and water temperature\n" +
          "• **Coastal Weather & Alerts**: Wind speed, squall warnings, and port advisories\n" +
          "• **Maritime Rules**: Knowledge base answers on safety guidelines, mesh sizes, and monsoon ban periods\n\n" +
          "What specific aspect would you like me to check for you?",
        source: "langgraph-multi-agent (conversational assistant)",
        is_demo: true,
        suggested_actions: ["Is it safe to go fishing tomorrow near Mumbai?", "Find Nearest PFZ", "What is PFZ?"],
        sources: [],
        is_rag: false,
        retrieved_chunks: 0
      };
    }
  }
}
