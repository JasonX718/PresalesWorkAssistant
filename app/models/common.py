"""
Common data models used across the application.
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OutputMode(str, Enum):
    """Output formatting mode based on target audience."""
    CUSTOMER = "customer"    # 客户模式 - 对外解释
    TECHNICAL = "technical"  # 技术模式 - 详细技术说明
    LEADERSHIP = "leadership"  # 领导模式 - 简洁汇总


class UrgencyLevel(str, Enum):
    """Urgency level for issues."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ScenarioType(str, Enum):
    """Available scenario modules."""
    TROUBLESHOOTING = "troubleshooting"
    TECH_QA = "tech_qa"
    CUSTOMER_REPLY = "customer_reply"
    WEEKLY_REPORT = "weekly_report"
    BRIEFING = "briefing"
    TRAINING = "training"
    DEMO_PREP = "demo_prep"
    POC_SUPPORT = "poc_support"
    ESCALATION = "escalation"


class ScenarioResult(BaseModel):
    """Standard output from any scenario module."""
    scenario: ScenarioType
    output_mode: OutputMode = OutputMode.TECHNICAL
    content: str
    structured_data: dict = Field(default_factory=dict)
    sources: list[str] = Field(default_factory=list)
    processing_time_seconds: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}
