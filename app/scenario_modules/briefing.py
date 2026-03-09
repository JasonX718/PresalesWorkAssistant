"""
Scenario Module 5: Briefing (汇报生成)

Generate structured briefing/presentation materials.
Time limit: 15 minutes.
"""

from app.scenario_modules.base import BaseScenarioModule
from app.models.common import ScenarioResult, ScenarioType, OutputMode
from app.prompt_templates.briefing import BRIEFING_SYSTEM_PROMPT, BRIEFING_USER_PROMPT
from config import get_settings


class BriefingModule(BaseScenarioModule):
    scenario_type = ScenarioType.BRIEFING

    def __init__(self):
        super().__init__()
        self.time_limit_seconds = get_settings().briefing_time_limit

    def _process(self, input_data: dict, output_mode: OutputMode) -> ScenarioResult:
        topic = input_data.get("topic", "")
        audience = input_data.get("audience", "技术团队")
        goal = input_data.get("goal", "")
        time_limit = input_data.get("time_limit", 30)

        knowledge_context = self.retrieve_knowledge(topic)

        user_prompt = BRIEFING_USER_PROMPT.format(
            topic=topic,
            audience=audience,
            goal=goal or "分享技术方案",
            time_limit=time_limit,
            knowledge_context=knowledge_context,
        )

        content = self.call_llm(
            BRIEFING_SYSTEM_PROMPT,
            user_prompt,
            output_mode,
        )

        return ScenarioResult(
            scenario=self.scenario_type,
            output_mode=output_mode,
            content=content,
            structured_data={
                "topic": topic,
                "audience": audience,
                "time_limit": time_limit,
            },
        )
