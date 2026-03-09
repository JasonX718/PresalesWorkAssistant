"""
Scenario Module 9: Problem Escalation (问题升级)

Generate structured escalation materials.
Time limit: 10 minutes.
"""

from app.scenario_modules.base import BaseScenarioModule
from app.models.common import ScenarioResult, ScenarioType, OutputMode
from app.prompt_templates.escalation import (
    ESCALATION_SYSTEM_PROMPT,
    ESCALATION_USER_PROMPT,
)
from config import get_settings


class EscalationModule(BaseScenarioModule):
    scenario_type = ScenarioType.ESCALATION

    def __init__(self):
        super().__init__()
        self.time_limit_seconds = get_settings().escalation_time_limit

    def _process(self, input_data: dict, output_mode: OutputMode) -> ScenarioResult:
        problem = input_data.get("problem", "")
        environment = input_data.get("environment", "")
        logs = input_data.get("logs", "")
        attempted_actions = input_data.get("attempted_actions", [])

        # Build knowledge query
        knowledge_query = f"{problem} {environment}"
        knowledge_context = self.retrieve_knowledge(knowledge_query)

        # Format attempted actions
        actions_str = "\n".join(
            f"{i+1}. {a}" for i, a in enumerate(attempted_actions)
        ) if attempted_actions else "无"

        user_prompt = ESCALATION_USER_PROMPT.format(
            problem=problem,
            environment=environment or "未提供",
            logs=logs or "未提供",
            attempted_actions=actions_str,
            knowledge_context=knowledge_context,
        )

        content = self.call_llm(
            ESCALATION_SYSTEM_PROMPT,
            user_prompt,
            output_mode,
        )

        return ScenarioResult(
            scenario=self.scenario_type,
            output_mode=output_mode,
            content=content,
            structured_data={
                "problem_summary": problem[:100],
                "actions_tried": len(attempted_actions),
            },
        )
