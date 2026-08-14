import logging
import time
from typing import Any, Optional

from backend.sub_agent.intent_recognize.intent_recognize import IntentResult
from backend.sub_agent.sub_agent_registry import SubAgentRegistry

logger = logging.getLogger(__name__)

class SubAgentExecutionResult:
    def __init__(self, success: bool, result: Any = None, error: Optional[str] = None, duration: float = 0.0):
        self.success = success
        self.result = result
        self.error = error
        self.duration = duration

class SubAgentScheduler:
    def __init__(self, registry: SubAgentRegistry, timeout: float = 30.0, max_retries: int = 0):
        self.registry = registry
        self.timeout = timeout
        self.max_retries = max_retries # name -> subagent实例


    def schedule(self, intent: IntentResult) -> SubAgentExecutionResult:
        start_time = time.time()
        attempt = 0
        last_error = None

        try:
            sub_agent = self.registry.get_sub_agent(intent.intent)
        except KeyError as e:
            return SubAgentExecutionResult(False, error=f"Sub-Agent by intent '{intent.intent}' not found", duration=0.0)

        while attempt <= self.max_retries:
            try:
                result = sub_agent.execute(intent)
                duration = time.time() - start_time
                self._log_success(sub_agent.name, intent, result, duration)
                return SubAgentExecutionResult(True, result=result, duration=duration)
            except Exception as e:
                last_error = e
                attempt += 1
                self._log_failure(sub_agent.name, intent, str(e), attempt)
                if attempt > self.max_retries:
                    break
                # 可选：根据异常类型决定是否重试
                if not self._is_retryable(e):
                    break

        duration = time.time() - start_time
        error_msg = f"Sub-Agent '{sub_agent.name}' failed after {attempt} attempts: {last_error}"
        return SubAgentExecutionResult(False, error=error_msg, duration=duration)

    @staticmethod
    def _is_retryable(exception: Exception) -> bool:
        # 自定义判断，例如网络超时可重试
        return isinstance(exception, (TimeoutError, ConnectionError))

    @staticmethod
    def _log_success(sub_agent_name, intent, result, duration):
        logger.info(f"Sub-Agent '{sub_agent_name}' succeeded in {duration:.2f}s, input={intent}, output={result}")

    @staticmethod
    def _log_failure(sub_agent_name, intent, error, attempt):
        logger.warning(f"Sub-Agent '{sub_agent_name}' failed on attempt {attempt}: {error}, input={intent}")