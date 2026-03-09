"""
Scenario Module 8: PoC Support (PoC支持)

Generate PoC plans and implementation guides.
"""

from app.scenario_modules.base import BaseScenarioModule
from app.models.common import ScenarioResult, ScenarioType, OutputMode
from app.prompt_templates.poc_support import POC_SUPPORT_SYSTEM_PROMPT, POC_SUPPORT_USER_PROMPT


class PocSupportModule(BaseScenarioModule):
    scenario_type = ScenarioType.POC_SUPPORT

    def _process(self, input_data: dict, output_mode: OutputMode) -> ScenarioResult:
        customer_requirements = input_data.get("customer_requirements", "")
        product_scope = input_data.get("product_scope", "")
        constraints = input_data.get("constraints", "")

        knowledge_context = self.retrieve_knowledge(
            f"{customer_requirements} {product_scope}"
        )

        user_prompt = POC_SUPPORT_USER_PROMPT.format(
            customer_requirements=customer_requirements,
            product_scope=product_scope or "ZStack Cloud 全功能",
            constraints=constraints or "无特殊约束",
            knowledge_context=knowledge_context,
        )

        content = self.call_llm(
            POC_SUPPORT_SYSTEM_PROMPT,
            user_prompt,
            output_mode,
        )

        return ScenarioResult(
            scenario=self.scenario_type,
            output_mode=output_mode,
            content=content,
            structured_data={
                "requirements_summary": customer_requirements[:100],
                "product_scope": product_scope,
            },
        )
