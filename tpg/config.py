from dotenv import load_dotenv

load_dotenv()

# Currently active LLM provider
# Trying out Anthropic Claude for now, since Ollama was lagging
LLM_PROVIDER = "claude"


# active model
OLLAMA_MODEL = "llama3.1:8b"
CLAUDE_MODEL = "claude-sonnet-5"
