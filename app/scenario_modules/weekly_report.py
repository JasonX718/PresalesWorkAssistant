"""
Scenario Module 4: Weekly Report (周报生成)

Generate structured weekly reports in multiple versions.
Time limit: 5 minutes.
"""

from app.scenario_modules.base import BaseScenarioModule
from app.models.common import ScenarioResult, ScenarioType, OutputMode
from app.prompt_templates.weekly_report import (
    WEEKLY_REPORT_SYSTEM_PROMPT,
    WEEKLY_REPORT_STANDARD_PROMPT,
    WEEKLY_REPORT_LEADERSHIP_PROMPT,
    WEEKLY_REPORT_TECHNICAL_PROMPT,
)
from config import get_settings


class WeeklyReportModule(BaseScenarioModule):
    scenario_type = ScenarioType.WEEKLY_REPORT

    def __init__(self):
        super().__init__()
        self.time_limit_seconds = get_settings().weekly_report_time_limit

    def _process(self, input_data: dict, output_mode: OutputMode) -> ScenarioResult:
        tasks_completed = input_data.get("tasks_completed", [])
        major_results = input_data.get("major_results", [])
        issues = input_data.get("issues", [])
        next_week_plan = input_data.get("next_week_plan", [])
        report_version = input_data.get("report_version", "standard")

        # Format list inputs
        tasks_str = "\n".join(f"- {t}" for t in tasks_completed) or "无"
        results_str = "\n".join(f"- {r}" for r in major_results) or "无"
        issues_str = "\n".join(f"- {i}" for i in issues) or "无"
        plan_str = "\n".join(f"- {p}" for p in next_week_plan) or "无"

        # Retrieve relevant knowledge (e.g., for context on issues)
        knowledge_query = " ".join(issues[:3]) if issues else " ".join(tasks_completed[:3])
        knowledge_context = self.retrieve_knowledge(knowledge_query) if knowledge_query else "无"

        # Select prompt template based on version
        if report_version == "leadership":
            prompt_template = WEEKLY_REPORT_LEADERSHIP_PROMPT
            output_mode = OutputMode.LEADERSHIP
        elif report_version == "technical":
            prompt_template = WEEKLY_REPORT_TECHNICAL_PROMPT
            output_mode = OutputMode.TECHNICAL
        else:
            prompt_template = WEEKLY_REPORT_STANDARD_PROMPT

        user_prompt = prompt_template.format(
            tasks_completed=tasks_str,
            major_results=results_str,
            issues=issues_str,
            next_week_plan=plan_str,
            knowledge_context=knowledge_context,
        )

        content = self.call_llm(
            WEEKLY_REPORT_SYSTEM_PROMPT,
            user_prompt,
            output_mode,
        )

        return ScenarioResult(
            scenario=self.scenario_type,
            output_mode=output_mode,
            content=content,
            structured_data={
                "version": report_version,
                "tasks_count": len(tasks_completed),
                "issues_count": len(issues),
            },
        )
