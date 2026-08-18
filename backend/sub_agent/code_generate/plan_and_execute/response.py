from typing import Literal

from pydantic import BaseModel, Field

resource_type_literal = Literal[
    "resource",
    "data_source",
]

class PlannerResponse(BaseModel):
    """Detail information for a resource."""
    resource_type: resource_type_literal = Field(description="The generated resource type， it can be resource or data_source.")