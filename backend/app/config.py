import os
from dotenv import load_dotenv

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "mock-key")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini")
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "true").lower() == "true"
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/mcp/")