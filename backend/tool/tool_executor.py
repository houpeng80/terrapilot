import json
import logging
import time
from typing import Any, Optional

from backend.tool.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)

class ToolExecutionResult:
    def __init__(self, success: bool, result: Any = None, error: Optional[str] = None, duration: float = 0.0):
        self.success = success
        self.result = result
        self.error = error
        self.duration = duration

class ToolExecutor:
    def __init__(self, registry: ToolRegistry, timeout: float = 30.0, max_retries: int = 0):
        self.registry = registry
        self.timeout = timeout
        self.max_retries = max_retries

    def execute(self, tool_name: str, tool_input: Any, **kwargs) -> ToolExecutionResult:
        """执行工具，返回统一结果对象"""
        start_time = time.time()
        attempt = 0
        last_error = None

        # 从注册表中获取工具，若不存在则直接返回失败
        try:
            tool = self.registry.get_tool(tool_name)
        except KeyError as e:
            return ToolExecutionResult(False, error=f"Tool '{tool_name}' not found", duration=0.0)

        while attempt <= self.max_retries:
            try:
                # 这里可以加入超时控制，例如使用 signal 或 concurrent.futures
                result = tool.invoke(tool_input, **kwargs)
                duration = time.time() - start_time
                self._log_success(tool_name, tool_input, result, duration)
                return ToolExecutionResult(True, result=json.dumps(result, ensure_ascii=False), duration=duration)
            except Exception as e:
                last_error = e
                attempt += 1
                self._log_failure(tool_name, tool_input, str(e), attempt)
                if attempt > self.max_retries:
                    break
                # 可选：根据异常类型决定是否重试
                if not self._is_retryable(e):
                    break

        duration = time.time() - start_time
        error_msg = f"Tool '{tool_name}' failed after {attempt} attempts: {last_error}"
        print("------------------------")
        return ToolExecutionResult(False, error=error_msg, duration=duration)

    @staticmethod
    def _is_retryable(exception: Exception) -> bool:
        # 自定义判断，例如网络超时可重试
        return isinstance(exception, (TimeoutError, ConnectionError))

    @staticmethod
    def _log_success(tool_name, tool_input, result, duration):
        logger.info(f"Tool '{tool_name}' succeeded in {duration:.2f}s, input={tool_input}, output={result}")

    @staticmethod
    def _log_failure(tool_name, tool_input, error, attempt):
        logger.warning(f"Tool '{tool_name}' failed on attempt {attempt}: {error}, input={tool_input}")