"""
AI Agent团队定义 - 模拟完整公司架构
"""
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from langchain_community.tools import DuckDuckGoSearchResultsTool
from dotenv import load_dotenv

load_dotenv()

# ==================== 工具定义 ====================

@tool("web_search")
def web_search(query: str) -> str:
    """搜索互联网获取最新信息"""
    search = DuckDuckGoSearchResultsTool()
    return search.run(query)

@tool("analyze_data")
def analyze_data(data: str) -> str:
    """分析数据并提供洞察"""
    return f"数据分析结果：{data[:500]}"

# ==================== Agent 工厂 ====================

class AgentTeam:
    """AI Agent团队"""

    def __init__(self):
        self.ceo = self._create_ceo()
        self.cto = self._create_cto()
        self.coo = self._create_coo()
        self.cmo = self._create_cmo()
        self.cpo = self._create_cpo()

    def _create_ceo(self):
        """CEO - 首席执行官"""
        return Agent(
            role="首席执行官 (CEO)",
            goal="制定公司战略，分析市场机会，做出关键决策",
            backstory="""
            您是公司的CEO，具有卓越的战略思维和商业洞察力。
            您负责制定公司整体战略，分析市场趋势，做出关键决策。
            您善于权衡利弊，能够在复杂情况下做出最优选择。
            """,
            verbose=True,
            allow_delegation=True
        )

    def _create_cto(self):
        """CTO - 首席技术官"""
        return Agent(
            role="首席技术官 (CTO)",
            goal="追踪前沿技术，研发创新解决方案",
            backstory="""
            您是公司的CTO，技术领域的专家。
            您负责技术研发，跟踪最新技术趋势，解决技术难题。
            您精通各种编程语言和开发工具。
            """,
            tools=[web_search, analyze_data],
            verbose=True,
            allow_delegation=True
        )

    def _create_coo(self):
        """COO - 首席运营官"""
        return Agent(
            role="首席运营官 (COO)",
            goal="优化运营效率，提升系统性能",
            backstory="""
            您是公司的COO，运营管理专家。
            您负责公司日常运营，优化流程，提升效率。
            您擅长数据分析，流程改进。
            """,
            tools=[analyze_data],
            verbose=True,
            allow_delegation=True
        )

    def _create_cmo(self):
        """CMO - 首席市场官"""
        return Agent(
            role="首席市场官 (CMO)",
            goal="分析市场动态，发现商业机会",
            backstory="""
            您是公司的CMO，市场营销专家。
            您负责市场分析，发现商业机会，评估竞争格局。
            您对市场趋势有敏锐的洞察力。
            """,
            tools=[web_search],
            verbose=True,
            allow_delegation=True
        )

    def _create_cpo(self):
        """CPO - 首席产品官"""
        return Agent(
            role="首席产品官 (CPO)",
            goal="开发产品，执行项目，交付价值",
            backstory="""
            您是公司的CPO，产品开发专家。
            您负责产品开发，项目执行，确保按时交付高质量产品。
            您熟悉各种开发方法和工具。
            """,
            tools=[analyze_data],
            verbose=True,
            allow_delegation=True
        )

    async def execute_task(self, task: str, mode: str = "auto") -> Dict[str, Any]:
        """执行任务"""

        if mode == "research" or mode == "auto":
            # 市场研究模式
            return await self._run_research(task)
        elif mode == "develop":
            # 开发模式
            return await self._run_develop(task)
        elif mode == "analyze":
            # 分析模式
            return await self._run_analyze(task)
        else:
            # 自动模式 - 根据任务类型自动选择
            return await self._run_auto(task)

    async def _run_research(self, task: str) -> Dict[str, Any]:
        """市场研究流程"""
        # CMO 分析市场
        market_task = Task(
            description=f"请深入分析以下市场领域：{task}\n\n要求：\n1. 市场规模和增长趋势\n2. 主要竞争对手分析\n3. 潜在机会和风险\n4. 建议的商业模式",
            agent=self.cmo,
            expected_output="详细的市场分析报告"
        )

        crew = Crew(
            agents=[self.cmo],
            tasks=[market_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()

        return {
            "mode": "research",
            "task": task,
            "result": str(result),
            "timestamp": datetime.now().isoformat()
        }

    async def _run_develop(self, task: str) -> Dict[str, Any]:
        """开发流程"""
        # CEO 制定策略
        # CTO 技术研发
        # CPO 执行开发

        tech_task = Task(
            description=f"请研究和设计以下技术方案：{task}\n\n要求：\n1. 技术架构设计\n2. 核心功能实现\n3. 代码示例\n4. 技术难点分析",
            agent=self.cto,
            expected_output="技术方案设计文档"
        )

        crew = Crew(
            agents=[self.cto],
            tasks=[tech_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()

        return {
            "mode": "develop",
            "task": task,
            "result": str(result),
            "timestamp": datetime.now().isoformat()
        }

    async def _run_analyze(self, task: str) -> Dict[str, Any]:
        """分析流程"""
        analysis_task = Task(
            description=f"请分析以下内容：{task}\n\n要求：\n1. 数据收集和整理\n2. 深度分析\n3. 洞察和建议\n4. 结论总结",
            agent=self.coo,
            expected_output="详细的分析报告"
        )

        crew = Crew(
            agents=[self.coo],
            tasks=[analysis_task],
            process=Process.sequential,
            verbose=True
        )

        result = crew.kickoff()

        return {
            "mode": "analyze",
            "task": task,
            "result": str(result),
            "timestamp": datetime.now().isoformat()
        }

    async def _run_auto(self, task: str) -> Dict[str, Any]:
        """自动流程 - 根据任务自动选择最佳流程"""

        # 模拟CEO决策
        decision_prompt = f"""请分析以下任务，确定最佳执行方式：

任务：{task}

请判断：
1. 这个任务更侧重于？（市场研究/技术开发/数据分析/综合分析）
2. 需要哪些角色参与？
3. 建议的执行流程？

直接给出分析结果，不需要其他内容。
"""

        # 简化处理
        if any(keyword in task for keyword in ["市场", "趋势", "机会", "竞争"]):
            return await self._run_research(task)
        elif any(keyword in task for keyword in ["开发", "代码", "技术", "系统"]):
            return await self._run_develop(task)
        elif any(keyword in task for keyword in ["分析", "数据", "报告"]):
            return await self._run_analyze(task)
        else:
            # 默认执行综合分析
            return await self._run_analyze(task)
