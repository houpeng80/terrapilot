import logging
import time

from backend.worker.worker_registry import WorkerRegistry
from backend.worker.workers import WorkerExecutionResult, WorkerRequest

logger = logging.getLogger(__name__)

class WorkerScheduler:
    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        self.registry = WorkerRegistry()
        self.timeout = timeout
        self.max_retries = max_retries

    def schedule(self, request: WorkerRequest) -> WorkerExecutionResult:
        start_time = time.time()
        attempt = 0
        last_error = None

        try:
            worker = self.registry.get_worker_by_intent(request.intent)
        except KeyError as e:
            return WorkerExecutionResult(False, error=f"Worker by intent '{request.intent}' not found", duration=0.0)

        while attempt < self.max_retries:
            try:
                result = worker.execute(intent=request)
                duration = time.time() - start_time
                self._log_success(worker.name, request, result, duration)
                return WorkerExecutionResult(True, result=result, duration=duration)
            except Exception as e:
                last_error = e
                attempt += 1
                self._log_failure(worker.name, request, str(e), attempt)
                if attempt > self.max_retries:
                    break
                # 可选：根据异常类型决定是否重试
                if not self._is_retryable(e):
                    break

        duration = time.time() - start_time
        error_msg = f"Worker '{worker.name}' failed after {attempt} attempts: {last_error}"
        return WorkerExecutionResult(False, error=error_msg, duration=duration)

    @staticmethod
    def _is_retryable(exception: Exception) -> bool:
        # 自定义判断，例如网络超时可重试
        return isinstance(exception, (TimeoutError, ConnectionError))

    @staticmethod
    def _log_success(sub_agent_name, intent, result, duration):
        logger.info(f"Worker '{sub_agent_name}' succeeded in {duration:.2f}s, input={intent}, output={result}")

    @staticmethod
    def _log_failure(sub_agent_name, intent, error, attempt):
        logger.warning(f"Worker '{sub_agent_name}' failed on attempt {attempt}: {error}, input={intent}")