"""
Scenario service layer.

High-level orchestration for scenario module execution.
"""

import logging

from app.models.common import ScenarioType, OutputMode, ScenarioResult
from app.router.scenario_router import route_scenario, detect_scenario, detect_scenario_with_llm

logger = logging.getLogger(__name__)


def execute_scenario(
    scenario_type: ScenarioType,
    input_data: dict,
    output_mode: OutputMode = OutputMode.TECHNICAL,
) -> ScenarioResult:
    """Execute a specific scenario module."""
    logger.info(f"Executing scenario: {scenario_type.value}, mode: {output_mode.value}")
    return route_scenario(scenario_type, input_data, output_mode)


def auto_execute(
    user_input: str,
    additional_data: dict = None,
    output_mode: OutputMode = OutputMode.TECHNICAL,
) -> ScenarioResult:
    """
    Auto-detect scenario from user input and execute.

    1. Try keyword-based detection
    2. Fall back to LLM-based detection
    3. Execute the detected scenario
    """
    # Try keyword detection first
    scenario = detect_scenario(user_input)

    if scenario is None:
        # Fall back to LLM
        logger.info("Keyword detection inconclusive, using LLM detection")
        scenario = detect_scenario_with_llm(user_input)

    logger.info(f"Auto-detected scenario: {scenario.value}")

    # Build input data
    input_data = additional_data or {}

    # Map user_input to the appropriate field based on scenario
    field_mapping = {
        ScenarioType.TROUBLESHOOTING: "problem_description",
        ScenarioType.TECH_QA: "question",
        ScenarioType.CUSTOMER_REPLY: "customer_question",
        ScenarioType.ESCALATION: "problem",
        ScenarioType.BRIEFING: "topic",
        ScenarioType.TRAINING: "training_topic",
        ScenarioType.DEMO_PREP: "demo_product",
        ScenarioType.POC_SUPPORT: "customer_requirements",
    }

    primary_field = field_mapping.get(scenario, "question")
    if primary_field not in input_data:
        input_data[primary_field] = user_input

    return route_scenario(scenario, input_data, output_mode)
