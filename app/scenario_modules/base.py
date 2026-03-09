"""
Base scenario module.

All scenario modules inherit from this base class.
Provides common functionality: knowledge retrieval, LLM calls, time limits.
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

from openai import OpenAI

from app.knowledge.vector_store import get_vector_store
from app.knowledge.embeddings import get_embedding_service
from app.models.common import ScenarioResult, ScenarioType, OutputMode
from app.prompt_templates.output_modes import get_output_mode_prompt
from config import get_settings

logger = logging.getLogger(__name__)


class BaseScenarioModule(ABC):
    """Base class for all scenario modules."""

    scenario_type: ScenarioType
    time_limit_seconds: int = 600  # default 10 minutes

    def __init__(self):
        settings = get_settings()
        self._llm_client = OpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )
        self._model = settings.llm_model

    def retrieve_knowledge(self, query: str, top_k: int = 5, where: Optional[dict] = None) -> str:
        """
        Retrieve relevant knowledge from the vector store.
        Returns formatted context string.
        """
        try:
            embedding_service = get_embedding_service()
            query_embedding = embedding_service.embed_query(query)

            store = get_vector_store()
            results = store.search(query_embedding, top_k=top_k, where=where)

            if not results:
                return "（未找到相关知识库内容）"

            context_parts = []
            for i, r in enumerate(results, 1):
                source = r["metadata"].get("source", "未知来源")
                title = r["metadata"].get("title", "")
                context_parts.append(
                    f"[知识库 #{i}] {title}\n来源: {source}\n{r['content']}"
                )

            return "\n\n---\n\n".join(context_parts)

        except Exception as e:
            logger.error(f"Knowledge retrieval error: {e}")
            return "（知识库检索异常）"

    def call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        output_mode: OutputMode = OutputMode.TECHNICAL,
        temperature: float = 0.3,
    ) -> str:
        """
        Call the LLM with system and user prompts.
        Appends output mode formatting instructions.
        """
        mode_prompt = get_output_mode_prompt(output_mode.value)
        full_system = f"{system_prompt}\n\n{mode_prompt}"

        try:
            response = self._llm_client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": full_system},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=4096,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"LLM call error: {e}")
            return f"LLM调用失败: {str(e)}"

    def execute(self, input_data: dict, output_mode: OutputMode = OutputMode.TECHNICAL) -> ScenarioResult:
        """
        Execute the scenario module with time tracking.

        Subclasses implement _process() for specific logic.
        """
        start_time = time.time()

        try:
            result = self._process(input_data, output_mode)
        except Exception as e:
            logger.error(f"Scenario {self.scenario_type} error: {e}")
            result = ScenarioResult(
                scenario=self.scenario_type,
                output_mode=output_mode,
                content=f"处理失败: {str(e)}",
            )

        result.processing_time_seconds = round(time.time() - start_time, 2)
        return result

    @abstractmethod
    def _process(self, input_data: dict, output_mode: OutputMode) -> ScenarioResult:
        """Process the scenario. Must be implemented by subclasses."""
        ...
