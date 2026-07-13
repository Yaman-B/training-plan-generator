import atexit
from typing import TypeVar

from anthropic import Anthropic, transform_schema
from ollama import chat
from pydantic import BaseModel, ValidationError

from tpg.config import CLAUDE_MODEL, LANGFUSE_ENABLED, LLM_PROVIDER, OLLAMA_MODEL
from tpg.tracing import observe

# LangFuse tracing
if LANGFUSE_ENABLED:
    from langfuse import get_client
    from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

    AnthropicInstrumentor().instrument() # liste to Anthropic API calls and send traces to LangFuse
    atexit.register(get_client().flush) # send any remaining traces to LangFuse on exit

_client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def _generate_ollama(prompt: str, format_schema: dict | None = None) -> str:
    """Talk to the local Ollama server and return the text reply.

    If format_schema is given, Ollama constrains output to that JSON schema.
    """
    response = chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        format=format_schema,
    )
    return response["message"]["content"]


def _generate_claude(prompt: str, format_schema: dict | None = None) -> str:
    """Talk to the Anthropic API and return the text reply.

    If format_schema is given, Claude constrains output to that JSON schema.
    """
    kwargs = {
        "model": CLAUDE_MODEL,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if format_schema is not None:
        kwargs["output_config"] = {
            "format": {"type": "json_schema", "schema": transform_schema(format_schema)}
        }

    response = _client.messages.create(**kwargs)
    return response.content[0].text


def generate(prompt: str, format_schema: dict | None = None) -> str:
    """The single door for all LLM calls.

    Routes to the active provider based on config.
    Pass format_schema (a JSON schema dict) to constrain output to that shape.
    """
    if LLM_PROVIDER == "ollama":
        return _generate_ollama(prompt, format_schema)
    if LLM_PROVIDER == "claude":
        return _generate_claude(prompt, format_schema)
    raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")


# Declaring type variable so that monthly and weekly plans can use the same function
T = TypeVar("T", bound=BaseModel)


@observe()
def generate_structured(prompt: str, schema: type[T], max_attempts: int = 3) -> T:
    """Call the LLM and validate its JSON output against `schema`.

    On a validation failure, feed the error back into the prompt and retry,
    up to max_attempts times. Raises if no attempt produces valid output.
    """
    format_schema = schema.model_json_schema()
    current_prompt = prompt
    last_error: ValidationError | None = None

    for _attempt in range(max_attempts):
        raw = generate(current_prompt, format_schema=format_schema)
        try:
            return schema.model_validate_json(raw)
        except ValidationError as err:
            last_error = err
            # Rebuild from the ORIGINAL prompt + only the latest error,
            current_prompt = (
                f"{prompt}\n\n"
                f"Your previous response was invalid. "
                f"Fix these problems and return corrected JSON:\n{err}"
            )

    raise ValueError(
        f"LLM failed to produce valid output after {max_attempts} attempts. "
        f"Last error:\n{last_error}"
    )
