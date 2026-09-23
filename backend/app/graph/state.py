from typing import TypedDict, Optional, List, Dict, Any

class MarineAgentState(TypedDict, total=False):
    """
    Shared state schema for MARINEX AI LangGraph multi-agent orchestration.
    Maintains user input, decomposed tasks, agent outputs, evidence, and final synthesis.
    """
    user_query: str
    chat_history: Optional[List[Dict[str, str]]]
    intent: Optional[str]
    location: Optional[Dict[str, Any]]
    time_context: Optional[Dict[str, Any]]
    tasks: List[str]
    selected_agents: List[str]
    rag_results: List[Dict[str, Any]]
    weather_results: Optional[Dict[str, Any]]
    ocean_results: Optional[Dict[str, Any]]
    geospatial_results: Optional[Dict[str, Any]]
    risk_results: Optional[Dict[str, Any]]
    evidence: List[str]
    intermediate_results: List[Dict[str, Any]]
    final_answer: Optional[str]
    response_type: Optional[str]
    errors: List[str]
    execution_steps: List[Dict[str, Any]]
    data_status: str
    map_data: Optional[Dict[str, Any]]
