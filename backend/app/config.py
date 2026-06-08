import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip()

USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"

MCP_SERVER_URL = os.getenv(
    "MCP_SERVER_URL",
    "https://mevzuat-mcp.bluesand-13d8735a.westus2.azurecontainerapps.io/mcp",
).strip()

MAX_TOOL_ROUNDS = int(os.getenv("MAX_TOOL_ROUNDS", "4"))

TOOL_RESULT_LIMITS = {
    "search_mevzuat": int(os.getenv("SEARCH_MEVZUAT_LIMIT", "1200")),
    "get_mevzuat_content": int(os.getenv("GET_CONTENT_LIMIT", "3000")),
    "search_within_mevzuat": int(os.getenv("SEARCH_WITHIN_LIMIT", "2000")),
    "get_mevzuat_madde_tree": int(os.getenv("MADDE_TREE_LIMIT", "1500")),
    "get_mevzuat_gerekce": int(os.getenv("GEREKCE_LIMIT", "2500")),
}