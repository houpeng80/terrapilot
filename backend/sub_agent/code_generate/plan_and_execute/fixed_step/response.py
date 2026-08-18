from typing import Any
from pydantic import  Field

from backend.sub_agent.code_generate.plan_and_execute.response import PlannerResponse

class FixedStepPlannerResponse(PlannerResponse):

    steps: Any = Field(description="The steps to be executed.")