import os

from dotenv import load_dotenv

load_dotenv()

# Currently active LLM provider
# Trying out Anthropic Claude for now, since Ollama was lagging
LLM_PROVIDER = "claude"


# active model
OLLAMA_MODEL = "llama3.1:8b"
CLAUDE_MODEL = "claude-sonnet-5"

# Langfuse tracing is optional: on only when its credentials are present, so the app
# still runs for anyone who clones the repo without them.
LANGFUSE_ENABLED = bool(
    os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")
)
