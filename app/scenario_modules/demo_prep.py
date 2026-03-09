"""
Scenario Module 7: Demo Preparation (演示准备)

Generate demo preparation plans and checklists.
"""

from app.scenario_modules.base import BaseScenarioModule
from app.models.common import ScenarioResult, ScenarioType, OutputMode
from app.prompt_templates.demo_prep import DEMO_PREP_SYSTEM_PROMPT, DEMO_PREP_USER_PROMPT


class DemoPrepModule(BaseScenarioModule):
    scenario_type = ScenarioType.DEMO_PREP

    def _process(self, input_data: dict, output_mode: OutputMode) -> ScenarioResult:
        demo_product = input_data.get("demo_product", "")
        scenario = input_data.get("scenario", "")
        audience = input_data.get("audience", "")
        time_limit = input_data.get("time_limit", 30)

        knowledge_context = self.retrieve_knowledge(f"{demo_product} {scenario}")

        user_prompt = DEMO_PREP_USER_PROMPT.format(
            demo_product=demo_product,
            scenario=scenario or "标准产品演示",
            audience=audience or "技术决策者",
            time_limit=time_limit,
            knowledge_context=knowledge_context,
        )

        content = self.call_llm(
            DEMO_PREP_SYSTEM_PROMPT,
            user_prompt,
            output_mode,
        )

        return ScenarioResult(
            scenario=self.scenario_type,
            output_mode=output_mode,
            content=content,
            structured_data={
                "product": demo_product,
                "scenario": scenario,
                "time_limit": time_limit,
            },
        )
