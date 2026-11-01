"""Provider-neutral contract. Live OpenAI integration is a pending task."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GenerationResult:
    content: dict
    provider: str
    model: str
    prompt_version: str


class ModelGateway(Protocol):
    async def generate_concept(self, brief: str) -> GenerationResult:
        """Return a schema-validated candidate, or raise an explicit error."""
        ...
