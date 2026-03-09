"""
Scenario module API endpoints.

POST /scenario/{scenario_type}  - Execute a specific scenario
POST /scenario/auto             - Auto-detect and execute scenario
GET  /scenario/types            - List available scenario types
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.models.common import ScenarioType, OutputMode
from app.models.scenarios import (
    TroubleshootingInput,
    TechQAInput,
    CustomerReplyInput,
    WeeklyReportInput,
    BriefingInput,
    TrainingInput,
    DemoPrepInput,
    PocSupportInput,
    EscalationInput,
)
from app.services.scenario_service import execute_scenario, auto_execute

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scenario", tags=["Scenario Modules"])


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
            {
                "type": s.value,
                "name": {
                    "troubleshooting": "技术问题排查",
                    "tech_qa": "技术问题回答",
                    "customer_reply": "客户答复",
                    "weekly_report": "周报生成",
                    "briefing": "汇报生成",
                    "training": "培训生成",
                    "demo_prep": "演示准备",
                    "poc_support": "PoC支持",
                    "escalation": "问题升级",
                }.get(s.value, s.value),
            }
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
        return ScenarioResponse(
            scenario=result.scenario.value,
            output_mode=result.output_mode.value,
            content=result.content,
            structured_data=result.structured_data,
            sources=result.sources,
            processing_time_seconds=result.processing_time_seconds,
        )
    except Exception as e:
        logger.error(f"Auto-execute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Specific Scenario Endpoints
# =============================================================================

@router.post("/troubleshooting", response_model=ScenarioResponse)
def api_troubleshooting(input_data: TroubleshootingInput):
    """Execute technical troubleshooting scenario."""
    try:
        result = execute_scenario(
            ScenarioType.TROUBLESHOOTING,
            input_data.model_dump(),
            input_data.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"Troubleshooting error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tech_qa", response_model=ScenarioResponse)
def api_tech_qa(input_data: TechQAInput):
    """Execute technical Q&A scenario."""
    try:
        result = execute_scenario(
            ScenarioType.TECH_QA,
            input_data.model_dump(),
            input_data.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"Tech QA error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customer_reply", response_model=ScenarioResponse)
def api_customer_reply(input_data: CustomerReplyInput):
    """Execute customer reply scenario."""
    try:
        result = execute_scenario(
            ScenarioType.CUSTOMER_REPLY,
            input_data.model_dump(),
            input_data.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"Customer reply error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/weekly_report", response_model=ScenarioResponse)
def api_weekly_report(input_data: WeeklyReportInput):
    """Execute weekly report generation scenario."""
    try:
        result = execute_scenario(
            ScenarioType.WEEKLY_REPORT,
            input_data.model_dump(),
            input_data.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"Weekly report error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/briefing", response_model=ScenarioResponse)
def api_briefing(input_data: BriefingInput):
    """Execute briefing generation scenario."""
    try:
        result = execute_scenario(
            ScenarioType.BRIEFING,
            input_data.model_dump(),
            input_data.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"Briefing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/training", response_model=ScenarioResponse)
def api_training(input_data: TrainingInput):
    """Execute training content generation scenario."""
    try:
        result = execute_scenario(
            ScenarioType.TRAINING,
            input_data.model_dump(),
            input_data.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/demo_prep", response_model=ScenarioResponse)
def api_demo_prep(input_data: DemoPrepInput):
    """Execute demo preparation scenario."""
    try:
        result = execute_scenario(
            ScenarioType.DEMO_PREP,
            input_data.model_dump(),
            input_data.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"Demo prep error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/poc_support", response_model=ScenarioResponse)
def api_poc_support(input_data: PocSupportInput):
    """Execute PoC support scenario."""
    try:
        result = execute_scenario(
            ScenarioType.POC_SUPPORT,
            input_data.model_dump(),
            input_data.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"PoC support error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/escalation", response_model=ScenarioResponse)
def api_escalation(input_data: EscalationInput):
    """Execute problem escalation scenario."""
    try:
        result = execute_scenario(
            ScenarioType.ESCALATION,
            input_data.model_dump(),
            input_data.output_mode,
        )
        return _to_response(result)
    except Exception as e:
        logger.error(f"Escalation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
