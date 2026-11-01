"""Provider-neutral generation contract."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GenerationResult:
    content: dict
    provider: str
    model: str
    prompt_version: str
    input_sha256: str = ''
    usage: dict | None = None


class GenerationError(RuntimeError):
    """Stable public error code; never includes upstream bodies or credentials."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class ModelGateway(Protocol):
    async def generate_concept(self, brief: str) -> GenerationResult:
        """Return a schema-validated candidate, or raise an explicit error."""
        ...
