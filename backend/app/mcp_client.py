from typing import Any

from fastmcp import Client

from app.config import MCP_SERVER_URL


class MCPClient:
    def __init__(self):
        self.client = Client(MCP_SERVER_URL)

    @staticmethod
    def _to_text(result: Any) -> str:
        data = getattr(result, "data", result)

        if data is None:
            return ""

        if isinstance(data, str):
            return data

        return str(data)

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        async with self.client:
            result = await self.client.call_tool(tool_name, arguments)

        return self._to_text(result)

    async def search_mevzuat(
        self,
        phrase: str | None = None,
        mevzuat_adi: str | None = None,
        mevzuat_no: str | None = None,
        mevzuat_tur: str | None = None,
        basliktaAra: bool = True,
        tamCumle: bool = False,
        resmi_gazete_tarihi: str | None = None,
        resmi_gazete_sayisi: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> str:
        arguments = {
            "basliktaAra": basliktaAra,
            "tamCumle": tamCumle,
            "page": page,
            "page_size": page_size,
        }

        optional_args = {
            "phrase": phrase,
            "mevzuat_adi": mevzuat_adi,
            "mevzuat_no": mevzuat_no,
            "mevzuat_tur": mevzuat_tur,
            "resmi_gazete_tarihi": resmi_gazete_tarihi,
            "resmi_gazete_sayisi": resmi_gazete_sayisi,
        }

        for key, value in optional_args.items():
            if value is not None and str(value).strip():
                arguments[key] = str(value).strip()

        return await self.call_tool("search_mevzuat", arguments)

    async def get_mevzuat_content(self, mevzuat_id: str) -> str:
        return await self.call_tool(
            "get_mevzuat_content",
            {
                "mevzuat_id": str(mevzuat_id),
            },
        )

    async def search_within_mevzuat(
        self,
        mevzuat_id: str,
        keyword: str,
        case_sensitive: bool = False,
        max_results: int = 10,
    ) -> str:
        return await self.call_tool(
            "search_within_mevzuat",
            {
                "mevzuat_id": str(mevzuat_id),
                "keyword": keyword,
                "case_sensitive": case_sensitive,
                "max_results": max_results,
            },
        )

    async def get_mevzuat_madde_tree(self, mevzuat_id: str) -> str:
        return await self.call_tool(
            "get_mevzuat_madde_tree",
            {
                "mevzuat_id": str(mevzuat_id),
            },
        )

    async def get_mevzuat_gerekce(self, gerekce_id: str) -> str:
        return await self.call_tool(
            "get_mevzuat_gerekce",
            {
                "gerekce_id": str(gerekce_id),
            },
        )