from ollama import chat
from tpg.config import LLM_PROVIDER, OLLAMA_MODEL


def _generate_ollama(prompt: str, format_schema: dict | None = None) -> str:
    """Talk to the local Ollama server and return the text reply.
    If format_schema is given, Ollama constrains output to that JSON schema."""
    response = chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        format=format_schema,
    )
    return response["message"]["content"]


def generate(prompt: str, format_schema: dict | None = None) -> str:
    """
    The single door for all LLM calls.
    Routes to the active provider based on config.
    Pass format_schema (a JSON schema dict) to constrain output to that shape.
    """
    if LLM_PROVIDER == "ollama":
        return _generate_ollama(prompt, format_schema)
    raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")
