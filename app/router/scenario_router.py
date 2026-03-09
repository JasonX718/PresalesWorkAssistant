"""
Scenario Router.

Routes user input to the appropriate scenario module.
Supports both explicit selection and automatic detection.
"""

import logging
from typing import Optional

from openai import OpenAI

from app.models.common import ScenarioType, OutputMode, ScenarioResult
from app.scenario_modules.troubleshooting import TroubleshootingModule
from app.scenario_modules.tech_qa import TechQAModule
from app.scenario_modules.customer_reply import CustomerReplyModule
from app.scenario_modules.weekly_report import WeeklyReportModule
from app.scenario_modules.briefing import BriefingModule
from app.scenario_modules.training import TrainingModule
from app.scenario_modules.demo_prep import DemoPrepModule
from app.scenario_modules.poc_support import PocSupportModule
from app.scenario_modules.escalation import EscalationModule
from config import get_settings

logger = logging.getLogger(__name__)

# Registry of all scenario modules
SCENARIO_MODULES = {
    ScenarioType.TROUBLESHOOTING: TroubleshootingModule,
    ScenarioType.TECH_QA: TechQAModule,
    ScenarioType.CUSTOMER_REPLY: CustomerReplyModule,
    ScenarioType.WEEKLY_REPORT: WeeklyReportModule,
    ScenarioType.BRIEFING: BriefingModule,
    ScenarioType.TRAINING: TrainingModule,
    ScenarioType.DEMO_PREP: DemoPrepModule,
    ScenarioType.POC_SUPPORT: PocSupportModule,
    ScenarioType.ESCALATION: EscalationModule,
}

# Keywords for auto-detection
SCENARIO_KEYWORDS = {
    ScenarioType.TROUBLESHOOTING: [
        "故障", "报错", "失败", "异常", "排查", "问题排查",
        "不工作", "宕机", "crash", "error", "fail", "troubleshoot",
    ],
    ScenarioType.TECH_QA: [
        "怎么", "如何", "什么是", "能不能", "支持", "兼容",
        "配置", "设置", "how to", "what is", "can",
    ],
    ScenarioType.CUSTOMER_REPLY: [
        "客户", "回复", "答复", "沟通", "customer", "reply",
    ],
    ScenarioType.WEEKLY_REPORT: [
        "周报", "周总结", "weekly report", "本周",
    ],
    ScenarioType.BRIEFING: [
        "汇报", "演讲", "PPT", "报告", "presentation", "briefing",
    ],
    ScenarioType.TRAINING: [
        "培训", "教学", "课程", "training", "教程",
    ],
    ScenarioType.DEMO_PREP: [
        "演示", "demo", "展示", "POC演示",
    ],
    ScenarioType.POC_SUPPORT: [
        "PoC", "概念验证", "测试方案", "试用",
    ],
    ScenarioType.ESCALATION: [
        "升级", "转交", "escalat", "上报", "需要支持",
    ],
}


def detect_scenario(text: str) -> Optional[ScenarioType]:
    """
    Auto-detect scenario type from user input text using keyword matching.
    Returns None if no scenario is confidently detected.
    """
    text_lower = text.lower()
    scores = {}

    for scenario, keywords in SCENARIO_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            scores[scenario] = score

    if not scores:
        return None

    # Return the highest-scoring scenario
    return max(scores, key=scores.get)


def detect_scenario_with_llm(text: str) -> ScenarioType:
    """
    Use LLM to detect the most appropriate scenario from user input.
    Fallback when keyword detection is not confident.
    """
    settings = get_settings()
    client = OpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    scenario_list = "\n".join(f"- {s.value}: {s.name}" for s in ScenarioType)

    prompt = f"""根据用户输入，判断最适合的场景模块。只返回场景名称，不要解释。

可选场景：
{scenario_list}

用户输入：
{text}

场景名称："""

    try:
        response = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=50,
        )
        result = response.choices[0].message.content.strip().lower()

        for scenario in ScenarioType:
            if scenario.value in result:
                return scenario

    except Exception as e:
        logger.error(f"LLM scenario detection error: {e}")

    # Default to tech_qa
    return ScenarioType.TECH_QA


def route_scenario(
    scenario_type: ScenarioType,
    input_data: dict,
    output_mode: OutputMode = OutputMode.TECHNICAL,
) -> ScenarioResult:
    """
    Route to the appropriate scenario module and execute.
    """
    module_class = SCENARIO_MODULES.get(scenario_type)
    if not module_class:
        return ScenarioResult(
            scenario=scenario_type,
            output_mode=output_mode,
            content=f"未知场景类型: {scenario_type.value}",
        )

    module = module_class()
    return module.execute(input_data, output_mode)
