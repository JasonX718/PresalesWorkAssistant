"""
Scenario Module 2: Technical Q&A (技术问题回答)

Quickly and accurately answer technical questions.
Time limit: 3 minutes.
"""

from app.scenario_modules.base import BaseScenarioModule
from app.models.common import ScenarioResult, ScenarioType, OutputMode
from app.prompt_templates.tech_qa import TECH_QA_SYSTEM_PROMPT, TECH_QA_USER_PROMPT
from config import get_settings


class TechQAModule(BaseScenarioModule):
    scenario_type = ScenarioType.TECH_QA

    def __init__(self):
        super().__init__()
        self.time_limit_seconds = get_settings().tech_qa_time_limit

    def _process(self, input_data: dict, output_mode: OutputMode) -> ScenarioResult:
        question = input_data.get("question", "")
        context = input_data.get("context", "")
        product = input_data.get("product", "ZStack")

        # Retrieve knowledge
        knowledge_query = f"{product} {question}"
        knowledge_context = self.retrieve_knowledge(knowledge_query)

        user_prompt = TECH_QA_USER_PROMPT.format(
            question=question,
            context=context or "无额外上下文",
            product=product,
            knowledge_context=knowledge_context,
        )

        content = self.call_llm(
            TECH_QA_SYSTEM_PROMPT,
            user_prompt,
            output_mode,
        )

        return ScenarioResult(
            scenario=self.scenario_type,
            output_mode=output_mode,
            content=content,
            structured_data={"question": question, "product": product},
        )
