from langchain.agents.middleware import TodoListMiddleware

SYSTEM_PROMPT = """
在开始任务前，必须先使用 write_todos 制定计划：
1. 将任务分解为多个可独立执行的子步骤
2. 按优先级排序
3. 每完成一步需更新状态

**关键规则：**
- todos一旦生成不能再更改
- 完成每个步骤后立即将待办事项标记为已完成 - 不要批量完成
- 随时将一项任务保留为“in_progress”，坚决不要并行执行任务
- 在工作时实时更新待办事项列表 - 这使用户可以了解您的进度
"""

class TodoMiddleware(TodoListMiddleware):

    def __init__(self):
        super(self.__class__, self).__init__(system_prompt=SYSTEM_PROMPT, tool_description="使用此工具创建、更新或删除你的任务清单")