"""
Scenario Module 1: Technical Troubleshooting (技术问题排查)

Quickly analyze technical issues and provide actionable solutions.
Time limit: 10 minutes.
"""

from app.scenario_modules.base import BaseScenarioModule
from app.models.common import ScenarioResult, ScenarioType, OutputMode
from app.prompt_templates.troubleshooting import (
    TROUBLESHOOTING_SYSTEM_PROMPT,
    TROUBLESHOOTING_USER_PROMPT,
)
from config import get_settings


class TroubleshootingModule(BaseScenarioModule):
    scenario_type = ScenarioType.TROUBLESHOOTING

    def __init__(self):
        super().__init__()
        self.time_limit_seconds = get_settings().troubleshooting_time_limit

    def _process(self, input_data: dict, output_mode: OutputMode) -> ScenarioResult:
        # Build knowledge query from problem description and component
        query_parts = [input_data.get("problem_description", "")]
        if input_data.get("affected_component"):
            query_parts.append(input_data["affected_component"])
        if input_data.get("error_logs"):
            # Use first 200 chars of logs for search relevance
            query_parts.append(input_data["error_logs"][:200])

        knowledge_query = " ".join(query_parts)
        knowledge_context = self.retrieve_knowledge(knowledge_query)

        # Build prompt
        user_prompt = TROUBLESHOOTING_USER_PROMPT.format(
            problem_description=input_data.get("problem_description", "未提供"),
            environment=input_data.get("environment", "未提供"),
            error_logs=input_data.get("error_logs", "未提供"),
            affected_component=input_data.get("affected_component", "未提供"),
            urgency_level=input_data.get("urgency_level", "medium"),
            knowledge_context=knowledge_context,
        )

        content = self.call_llm(
            TROUBLESHOOTING_SYSTEM_PROMPT,
            user_prompt,
            output_mode,
        )

        return ScenarioResult(
            scenario=self.scenario_type,
            output_mode=output_mode,
            content=content,
            structured_data={
                "problem": input_data.get("problem_description", ""),
                "urgency": input_data.get("urgency_level", "medium"),
            },
        )
