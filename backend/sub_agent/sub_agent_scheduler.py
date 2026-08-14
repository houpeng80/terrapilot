import threading
from typing import Dict, Any, Optional


class SubAgentExecutionResult:
    def __init__(self, success: bool, result: Any = None, error: Optional[str] = None, duration: float = 0.0):
        self.success = success
        self.result = result
        self.error = error
        self.duration = duration

class SubAgentScheduler:
    def __init__(self):
        self._lock = threading.RLock()
        self.sub_agents = Dict[str, Any] = {}  # name -> subagent实例


    async def schedule(self, agent_names: List[str], ctx: MainAgentContext) -> List[SubAgentResult]:
        tasks = []
        for name in agent_names:
            agent = self.sub_agents[name]
            tasks.append(agent.run(ctx))
        # 并行调用多个子agent
        results = await asyncio.gather(*tasks, return_exceptions=True)
        output = []
        for r in results:
            if isinstance(r, Exception):
                output.append(SubAgentResult(
                    sub_agent_name="unknown", success=False,
                    intent_tag="", raw_content="", summary="", error=str(r)
                ))
            else:
                output.append(r)
        return output