"""
Scenario module input/output models.
"""

from pydantic import BaseModel, Field
from typing import Optional
from app.models.common import OutputMode, UrgencyLevel


# =============================================================================
# Module 1: Troubleshooting (技术问题排查)
# =============================================================================

class TroubleshootingInput(BaseModel):
    """Input for technical troubleshooting."""
    problem_description: str
    environment: str = ""
    error_logs: str = ""
    affected_component: str = ""
    urgency_level: UrgencyLevel = UrgencyLevel.MEDIUM
    output_mode: OutputMode = OutputMode.TECHNICAL


# =============================================================================
# Module 2: Tech Q&A (技术问题回答)
# =============================================================================

class TechQAInput(BaseModel):
    """Input for technical Q&A."""
    question: str
    context: str = ""
    product: str = "ZStack"
    output_mode: OutputMode = OutputMode.TECHNICAL


# =============================================================================
# Module 3: Customer Reply (客户答复)
# =============================================================================

class CustomerReplyInput(BaseModel):
    """Input for customer reply generation."""
    customer_question: str
    context: str = ""
    product: str = "ZStack"
    output_mode: OutputMode = OutputMode.CUSTOMER


# =============================================================================
# Module 4: Weekly Report (周报生成)
# =============================================================================

class WeeklyReportInput(BaseModel):
    """Input for weekly report generation."""
    tasks_completed: list[str] = Field(default_factory=list)
    major_results: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    next_week_plan: list[str] = Field(default_factory=list)
    report_version: str = "standard"   # standard | leadership | technical
    output_mode: OutputMode = OutputMode.LEADERSHIP


# =============================================================================
# Module 5: Briefing (汇报生成)
# =============================================================================

class BriefingInput(BaseModel):
    """Input for briefing/presentation generation."""
    topic: str
    audience: str = ""
    goal: str = ""
    time_limit: int = 30   # minutes
    output_mode: OutputMode = OutputMode.LEADERSHIP


# =============================================================================
# Module 6: Training (培训生成)
# =============================================================================

class TrainingInput(BaseModel):
    """Input for training content generation."""
    training_topic: str
    audience_level: str = "intermediate"   # beginner | intermediate | advanced
    duration: int = 60   # minutes
    output_mode: OutputMode = OutputMode.TECHNICAL


# =============================================================================
# Module 7: Demo Preparation (演示准备)
# =============================================================================

class DemoPrepInput(BaseModel):
    """Input for demo preparation."""
    demo_product: str
    scenario: str = ""
    audience: str = ""
    time_limit: int = 30   # minutes
    output_mode: OutputMode = OutputMode.TECHNICAL


# =============================================================================
# Module 8: PoC Support (PoC支持)
# =============================================================================

class PocSupportInput(BaseModel):
    """Input for PoC support."""
    customer_requirements: str
    product_scope: str = ""
    constraints: str = ""
    output_mode: OutputMode = OutputMode.TECHNICAL


# =============================================================================
# Module 9: Escalation (问题升级)
# =============================================================================

class EscalationInput(BaseModel):
    """Input for problem escalation."""
    problem: str
    environment: str = ""
    logs: str = ""
    attempted_actions: list[str] = Field(default_factory=list)
    output_mode: OutputMode = OutputMode.TECHNICAL
