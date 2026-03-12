"""
Scenario module API endpoints.

POST /scenario/{scenario_type}  - Execute a specific scenario (dynamic routing)
POST /scenario/auto             - Auto-detect and execute scenario
GET  /scenario/types            - List available scenario types
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.common import OutputMode, ScenarioType
from app.models.scenarios import (
    BriefingInput,
    CustomerReplyInput,
    DemoPrepInput,
    EscalationInput,
    PocSupportInput,
    TechQAInput,
    TrainingInput,
    TroubleshootingInput,
    WeeklyReportInput,
)
from app.services.scenario_service import auto_execute, execute_scenario

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scenario", tags=["Scenario Modules"])

# =============================================================================
# Scenario name → display label mapping
# =============================================================================

SCENARIO_LABELS: dict[str, str] = {
    "troubleshooting": "技术问题排查",
    "tech_qa": "技术问题回答",
    "customer_reply": "客户答复",
    "weekly_report": "周报生成",
    "briefing": "汇报生成",
    "training": "培训生成",
    "demo_prep": "演示准备",
    "poc_support": "PoC支持",
    "escalation": "问题升级",
}

# Scenario type → Pydantic input model mapping (for validation)
SCENARIO_INPUT_MODELS: dict[ScenarioType, type[BaseModel]] = {
    ScenarioType.TROUBLESHOOTING: TroubleshootingInput,
    ScenarioType.TECH_QA: TechQAInput,
    ScenarioType.CUSTOMER_REPLY: CustomerReplyInput,
    ScenarioType.WEEKLY_REPORT: WeeklyReportInput,
    ScenarioType.BRIEFING: BriefingInput,
    ScenarioType.TRAINING: TrainingInput,
    ScenarioType.DEMO_PREP: DemoPrepInput,
    ScenarioType.POC_SUPPORT: PocSupportInput,
    ScenarioType.ESCALATION: EscalationInput,
}


# =============================================================================
# Response Model
# =============================================================================


class AutoDetectRequest(BaseModel):
    """Request for auto-detection scenario execution."""

    input_text: str = Field(..., description="User input text for auto-detection")
    additional_data: dict = Field(default_factory=dict, description="Additional structured data")
    output_mode: OutputMode = OutputMode.TECHNICAL


class ScenarioResponse(BaseModel):
    """Response from scenario execution."""

    scenario: str
    output_mode: str
    content: str
    structured_data: dict = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    processing_time_seconds: float = 0.0


# =============================================================================
# Available Scenario Types
# =============================================================================


@router.get("/types")
def api_list_scenarios():
    """List all available scenario types."""
    return {
        "scenarios": [
            {"type": s.value, "name": SCENARIO_LABELS.get(s.value, s.value)}
            for s in ScenarioType
        ]
    }


# =============================================================================
# Auto-Detect Execution
# =============================================================================


@router.post("/auto", response_model=ScenarioResponse)
def api_auto_execute(request: AutoDetectRequest):
    """
    Auto-detect scenario from input text and execute.

    The system analyzes the input to determine the most appropriate
    scenario module, then executes it.
    """
    try:
        result = auto_execute(
            user_input=request.input_text,
            additional_data=request.additional_data,
            output_mode=request.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"Auto-execute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Dynamic Scenario Endpoint — replaces 9 near-identical endpoints
# =============================================================================


@router.post("/{scenario_type}", response_model=ScenarioResponse)
def api_execute_scenario(scenario_type: ScenarioType, input_data: dict):
    """
    Execute any scenario module by type.

    Accepts the scenario type as a path parameter and validates input
    against the corresponding Pydantic model before execution.

    Supported scenario types:
    - troubleshooting, tech_qa, customer_reply, weekly_report,
      briefing, training, demo_prep, poc_support, escalation
    """
    # Validate input against the correct model
    model_class = SCENARIO_INPUT_MODELS.get(scenario_type)
    if not model_class:
        raise HTTPException(status_code=404, detail=f"Unknown scenario type: {scenario_type}")

    try:
        validated = model_class(**input_data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Input validation failed: {e}")

    try:
        result = execute_scenario(
            scenario_type,
            validated.model_dump(),
            validated.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"{scenario_type.value} error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Helpers
# =============================================================================


def _to_response(result) -> ScenarioResponse:
    """Convert ScenarioResult to ScenarioResponse."""
    return ScenarioResponse(
        scenario=result.scenario.value,
        output_mode=result.output_mode.value,
        content=result.content,
        structured_data=result.structured_data,
        sources=result.sources,
        processing_time_seconds=result.processing_time_seconds,
    )
