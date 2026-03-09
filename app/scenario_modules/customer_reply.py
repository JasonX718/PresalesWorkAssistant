"""
Scenario Module 3: Customer Reply (客户答复)

Generate professional customer-facing replies.
"""

from app.scenario_modules.base import BaseScenarioModule
from app.models.common import ScenarioResult, ScenarioType, OutputMode
from app.prompt_templates.customer_reply import (
    CUSTOMER_REPLY_SYSTEM_PROMPT,
    CUSTOMER_REPLY_USER_PROMPT,
)


class CustomerReplyModule(BaseScenarioModule):
    scenario_type = ScenarioType.CUSTOMER_REPLY

    def _process(self, input_data: dict, output_mode: OutputMode) -> ScenarioResult:
        customer_question = input_data.get("customer_question", "")
        context = input_data.get("context", "")
        product = input_data.get("product", "ZStack")

        knowledge_context = self.retrieve_knowledge(f"{product} {customer_question}")

        user_prompt = CUSTOMER_REPLY_USER_PROMPT.format(
            customer_question=customer_question,
            context=context or "无额外上下文",
            product=product,
            knowledge_context=knowledge_context,
        )

        # Customer replies default to customer output mode
        actual_mode = output_mode if output_mode != OutputMode.TECHNICAL else OutputMode.CUSTOMER

        content = self.call_llm(
            CUSTOMER_REPLY_SYSTEM_PROMPT,
            user_prompt,
            actual_mode,
        )

        return ScenarioResult(
            scenario=self.scenario_type,
            output_mode=actual_mode,
            content=content,
            structured_data={
                "customer_question": customer_question,
                "product": product,
            },
        )
