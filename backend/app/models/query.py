"""Query request models."""

from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    """Natural-language retrieval request."""

    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=4, ge=1, le=10)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "What does the policy say about remote work?",
                "top_k": 4,
            }
        }
    )

