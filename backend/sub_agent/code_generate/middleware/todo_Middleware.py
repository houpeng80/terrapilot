from __future__ import annotations

from langchain.agents.middleware import TodoListMiddleware

SYSTEM_PROMPT = """
<todo_list_system>
## `write_todos`
You have access to the `write_todos` tool to help you manage and track complex multi-step objectives.

## CRITICAL RULES:
- create a todos task depends on the step before executing the task, do not add extra step, nor omit existing ones
- execute the todos step-by-step, the next step can only proceed once the current one has completed
- Mark todos as completed IMMEDIATELY after finishing each step - do NOT batch completions
- Keep EXACTLY ONE task as `in_progress` at any time (unless tasks can run in parallel)

## When to Use:
Use it when generate terraform code, test and doc

## Finish task:
When you finish all work, write your final answer in the message AFTER your last `write_todos` call — not in the same turn as that call.
Start the final message with the substantive content the user asked for — the data, computation, summary, or analysis.
The user wants the result, not confirmation that the work is done.
</todo_list_system>
"""

class TodoMiddleware(TodoListMiddleware):

    def __init__(self, agent_name: str | None = None):
        super(self.__class__, self).__init__(system_prompt=SYSTEM_PROMPT)
        self._agent_name = agent_name