from fastmcp import Client
from app.config import MCP_SERVER_URL


class MCPClient:
    def __init__(self):
        self.client = Client(MCP_SERVER_URL)

    async def search_mevzuat(self, query: str):
        async with self.client:
            return await self.client.call_tool(
                "search_mevzuat",
                {
                    "mevzuat_adi": query,
                    "page_size": 20
                }
            )

    async def get_mevzuat_content(self, mevzuat_id: str):
        async with self.client:
            return await self.client.call_tool(
                "get_mevzuat_content",
                {
                    "mevzuat_id": str(mevzuat_id)
                }
            )

    async def search_within_mevzuat(self, mevzuat_id: str, keyword: str):
        async with self.client:
            return await self.client.call_tool(
                "search_within_mevzuat",
                {
                    "mevzuat_id": str(mevzuat_id),
                    "keyword": keyword,
                    "case_sensitive": False,
                    "max_results": 10
                }
            )

    async def get_mevzuat_madde_tree(self, mevzuat_id: str):
        async with self.client:
            return await self.client.call_tool(
                "get_mevzuat_madde_tree",
                {
                    "mevzuat_id": str(mevzuat_id)
                }
            )

    async def get_mevzuat_gerekce(self, gerekce_id: str):
        async with self.client:
            return await self.client.call_tool(
                "get_mevzuat_gerekce",
                {
                    "gerekce_id": str(gerekce_id)
                }
            )