"""
Example API requests for AI Work Assistant.

Run after starting the server: python main.py
Then execute this script: python examples/example_requests.py
"""

import httpx
import json

BASE_URL = "http://localhost:8000"


def print_response(title: str, response):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    print(f"Status: {response.status_code}")
    try:
        data = response.json()
        if "content" in data:
            print(f"\n{data['content'][:2000]}")
            print(f"\n[Processing time: {data.get('processing_time_seconds', 'N/A')}s]")
        else:
            print(json.dumps(data, indent=2, ensure_ascii=False)[:2000])
    except Exception:
        print(response.text[:1000])
    print()


def main():
    client = httpx.Client(base_url=BASE_URL, timeout=120)

    # =========================================================================
    # 1. Health Check
    # =========================================================================
    print_response("Health Check", client.get("/health"))

    # =========================================================================
    # 2. Bootstrap Knowledge Base
    # =========================================================================
    print_response(
        "Bootstrap Knowledge Base",
        client.post("/knowledge/bootstrap"),
    )

    # =========================================================================
    # 3. Search Knowledge Base
    # =========================================================================
    print_response(
        "Search: ZStack高可用",
        client.get("/knowledge/search", params={"query": "ZStack高可用部署方案"}),
    )

    # =========================================================================
    # 4. Technical Troubleshooting
    # =========================================================================
    print_response(
        "Scenario: 技术问题排查",
        client.post("/scenario/troubleshooting", json={
            "problem_description": "客户环境中云主机创建失败，提示存储空间不足",
            "environment": "ZStack 4.6.0, CentOS 7.9, Ceph存储, 3节点集群",
            "error_logs": "Error: not enough space on primary storage",
            "affected_component": "PrimaryStorage",
            "urgency_level": "high",
            "output_mode": "technical",
        }),
    )

    # =========================================================================
    # 5. Technical Q&A
    # =========================================================================
    print_response(
        "Scenario: 技术问答",
        client.post("/scenario/tech_qa", json={
            "question": "ZStack支持哪些存储方案？生产环境推荐用什么？",
            "product": "ZStack Cloud",
            "output_mode": "technical",
        }),
    )

    # =========================================================================
    # 6. Customer Reply
    # =========================================================================
    print_response(
        "Scenario: 客户答复",
        client.post("/scenario/customer_reply", json={
            "customer_question": "我们公司有50台服务器，想部署私有云，ZStack能满足需求吗？大概需要多少成本？",
            "context": "客户是制造业，IT团队5人，没有云计算经验",
            "product": "ZStack Cloud",
            "output_mode": "customer",
        }),
    )

    # =========================================================================
    # 7. Weekly Report
    # =========================================================================
    print_response(
        "Scenario: 周报生成（领导版）",
        client.post("/scenario/weekly_report", json={
            "tasks_completed": [
                "完成客户A的ZStack Cloud PoC部署",
                "处理了3个技术支持工单",
                "参加产品培训并通过考试",
                "编写了Ceph存储最佳实践文档",
            ],
            "major_results": [
                "客户A PoC成功通过验收，预计下月签约",
                "工单平均处理时间缩短20%",
            ],
            "issues": [
                "客户B的VPC网络偶现延迟问题，正在排查",
            ],
            "next_week_plan": [
                "准备客户C的技术方案汇报",
                "跟进客户A的商务流程",
                "完成新版本功能测试",
            ],
            "report_version": "leadership",
            "output_mode": "leadership",
        }),
    )

    # =========================================================================
    # 8. Problem Escalation
    # =========================================================================
    print_response(
        "Scenario: 问题升级",
        client.post("/scenario/escalation", json={
            "problem": "客户生产环境管理节点频繁重启，每天2-3次，已持续一周",
            "environment": "ZStack 4.5.0, 双管理节点HA, MySQL Galera, 20台物理机",
            "logs": "OutOfMemoryError: Java heap space\nat java.lang.Thread.run(Thread.java:748)",
            "attempted_actions": [
                "检查了MySQL连接数，正常",
                "增加了JVM堆内存从4G到8G，问题缓解但未解决",
                "排查了RabbitMQ消息队列，未发现堆积",
                "检查了所有定时任务，未发现异常",
            ],
            "output_mode": "technical",
        }),
    )

    # =========================================================================
    # 9. Auto-Detect Scenario
    # =========================================================================
    print_response(
        "Scenario: 自动识别",
        client.post("/scenario/auto", json={
            "input_text": "客户问ZStack能不能对接他们现有的VMware环境，实现统一管理",
            "output_mode": "customer",
        }),
    )

    # =========================================================================
    # 10. Knowledge Base Stats
    # =========================================================================
    print_response(
        "Knowledge Base Stats",
        client.get("/knowledge/stats"),
    )

    print("\n" + "=" * 60)
    print("  All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
