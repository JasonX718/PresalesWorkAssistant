"""
Scenario Module 6: Training (培训生成)

Generate structured training content materials.
"""

from app.scenario_modules.base import BaseScenarioModule
from app.models.common import ScenarioResult, ScenarioType, OutputMode
from app.prompt_templates.training import TRAINING_SYSTEM_PROMPT, TRAINING_USER_PROMPT


class TrainingModule(BaseScenarioModule):
    scenario_type = ScenarioType.TRAINING

    def _process(self, input_data: dict, output_mode: OutputMode) -> ScenarioResult:
        training_topic = input_data.get("training_topic", "")
        audience_level = input_data.get("audience_level", "intermediate")
        duration = input_data.get("duration", 60)

        knowledge_context = self.retrieve_knowledge(training_topic)

        # Calculate time allocation
        intro_time = max(5, int(duration * 0.15))
        main_time = max(15, int(duration * 0.45))
        practice_time = max(10, int(duration * 0.25))
        qa_time = max(5, int(duration * 0.15))

        user_prompt = TRAINING_USER_PROMPT.format(
            training_topic=training_topic,
            audience_level=audience_level,
            duration=duration,
            knowledge_context=knowledge_context,
            intro_time=intro_time,
            main_time=main_time,
            practice_time=practice_time,
            qa_time=qa_time,
        )

        content = self.call_llm(
            TRAINING_SYSTEM_PROMPT,
            user_prompt,
            output_mode,
        )

        return ScenarioResult(
            scenario=self.scenario_type,
            output_mode=output_mode,
            content=content,
            structured_data={
                "topic": training_topic,
                "level": audience_level,
                "duration": duration,
            },
        )
