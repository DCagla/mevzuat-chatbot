import re
from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL, USE_MOCK_LLM
from app.mcp_client import MCPClient


class LLMService:
    def __init__(self):
        self.mcp_client = MCPClient()
        self.openai_client = None

        if not USE_MOCK_LLM and OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=OPENAI_API_KEY)

    async def process_message(self, message: str) -> str:
        if USE_MOCK_LLM:
            return await self._mock_agent_response(message)

        return await self._openai_agent_response(message)

    async def _mock_agent_response(self, message: str) -> str:
        search_query = self._extract_law_query(message)

        search_result = await self.mcp_client.search_mevzuat(search_query)
        search_text = search_result.data

        mevzuat_id = self._extract_preferred_mevzuat_id(search_text)
        gerekce_id = self._extract_gerekce_id(search_text)

        if not mevzuat_id:
            return (
                f"'{message}' sorusu için '{search_query}' ifadesiyle arama yaptım.\n\n"
                f"Sonuç:\n\n{search_text}\n\n"
                f"Not: İlgili mevzuatId bulunamadığı için diğer MCP tool'ları çağrılamadı."
            )

        if self._asks_for_gerekce(message):
            if gerekce_id:
                gerekce_result = await self.mcp_client.get_mevzuat_gerekce(gerekce_id)
                return (
                    f"'{message}' sorusu gerekçe ile ilgili olduğu için şu MCP tool'ları kullanıldı:\n\n"
                    f"1. search_mevzuat\n"
                    f"2. get_mevzuat_gerekce\n\n"
                    f"gerekceId: {gerekce_id}\n\n"
                    f"Sonuç:\n\n{gerekce_result.data[:2500]}\n\n"
                    f"Not: Mock LLM modu aktif."
                )

            return (
                f"'{message}' sorusu gerekçe ile ilgili göründü.\n\n"
                f"1. search_mevzuat tool'u çalıştırıldı.\n"
                f"2. Ancak arama sonucunda gerekceId bulunamadığı için get_mevzuat_gerekce çağrılamadı.\n\n"
                f"Arama sonucu:\n\n{search_text}\n\n"
                f"Not: Mock LLM modu aktif."
            )

        if self._asks_for_search_within(message):
            keyword = self._extract_keyword_for_within_search(message)
            within_result = await self.mcp_client.search_within_mevzuat(mevzuat_id, keyword)

            return (
                f"'{message}' sorusu mevzuat içinde konu araması gerektirdiği için şu MCP tool'ları kullanıldı:\n\n"
                f"1. search_mevzuat\n"
                f"2. search_within_mevzuat\n\n"
                f"mevzuatId: {mevzuat_id}\n"
                f"Aranan ifade: {keyword}\n\n"
                f"Mevzuat içinde bulunan sonuçlar:\n\n{within_result.data[:3000]}\n\n"
                f"Not: Mock LLM modu aktif."
            )

        if self._asks_for_tree(message):
            tree_result = await self.mcp_client.get_mevzuat_madde_tree(mevzuat_id)
            return (
                f"'{message}' sorusu madde ağacı / madde listesi ile ilgili olduğu için şu MCP tool'ları kullanıldı:\n\n"
                f"1. search_mevzuat\n"
                f"2. get_mevzuat_madde_tree\n\n"
                f"mevzuatId: {mevzuat_id}\n\n"
                f"Madde ağacı sonucu:\n\n{tree_result.data[:3000]}\n\n"
                f"Not: Mock LLM modu aktif."
            )

        if self._should_fetch_content(message):
            content_result = await self.mcp_client.get_mevzuat_content(mevzuat_id)

            return (
                f"'{message}' sorusu mevzuat içeriği gerektirdiği için şu MCP tool'ları kullanıldı:\n\n"
                f"1. search_mevzuat\n"
                f"2. get_mevzuat_content\n\n"
                f"mevzuatId: {mevzuat_id}\n\n"
                f"İçerikten ilk bölüm:\n\n{content_result.data[:2500]}\n\n"
                f"Not: Mock LLM modu aktif."
            )

        return (
            f"'{message}' sorgusu için şu MCP tool kullanıldı:\n\n"
            f"1. search_mevzuat\n\n"
            f"Arama sonucu:\n\n{search_text}\n\n"
            f"Not: Mock LLM modu aktif."
        )

    async def _openai_agent_response(self, message: str) -> str:
        search_query = self._extract_law_query(message)

        search_result = await self.mcp_client.search_mevzuat(search_query)
        search_context = search_result.data

        mevzuat_id = self._extract_preferred_mevzuat_id(search_context)
        gerekce_id = self._extract_gerekce_id(search_context)

        tool_outputs = [f"search_mevzuat result:\n{search_context}"]

        if mevzuat_id:
            if self._asks_for_gerekce(message) and gerekce_id:
                gerekce_result = await self.mcp_client.get_mevzuat_gerekce(gerekce_id)
                tool_outputs.append(
                    f"get_mevzuat_gerekce result:\n{gerekce_result.data[:6000]}"
                )

            elif self._asks_for_search_within(message):
                keyword = self._extract_keyword_for_within_search(message)
                within_result = await self.mcp_client.search_within_mevzuat(mevzuat_id, keyword)
                tool_outputs.append(
                    f"search_within_mevzuat result:\n{within_result.data[:6000]}"
                )

            elif self._asks_for_tree(message):
                tree_result = await self.mcp_client.get_mevzuat_madde_tree(mevzuat_id)
                tool_outputs.append(
                    f"get_mevzuat_madde_tree result:\n{tree_result.data[:6000]}"
                )

            else:
                content_result = await self.mcp_client.get_mevzuat_content(mevzuat_id)
                tool_outputs.append(
                    f"get_mevzuat_content result:\n{content_result.data[:8000]}"
                )

        prompt = f"""
Kullanıcı sorusu:
{message}

Kullanılan MCP tool sonuçları:
{chr(10).join(tool_outputs)}

Görev:
Görev:
Kullanıcının sorusuna Türkçe ve kullanıcı dostu şekilde cevap ver.
MCP tool isimlerinden, teknik detaylardan veya sistem çıktılarından bahsetme.
Kullanıcıya yalnızca mevzuat bilgisini aktar.
Cevabını yalnızca MCP tool sonuçlarına dayandır.
Uydurma bilgi verme.
Elindeki MCP sonuçlarında bulunmayan bilgileri ekleme veya vaat etme.
Eğer bilgi eksikse bunu kısa şekilde belirt.
En fazla 5-7 cümle kullan.
"""

        response = self.openai_client.responses.create(
            model=OPENAI_MODEL,
            input=prompt,
            max_output_tokens=400
        )

        return response.output_text

    def _normalize_turkish(self, text: str) -> str:
        return text.strip().replace("İ", "i").replace("I", "ı").lower()

    def _extract_law_query(self, message: str) -> str:
        lower = self._normalize_turkish(message)

        known_laws = [
            "iş kanunu",
            "kişisel verilerin korunması kanunu",
            "kvkk",
            "türk borçlar kanunu",
            "türk ceza kanunu",
            "ticaret kanunu",
            "deniz iş kanunu",
        ]

        for law in known_laws:
            if law in lower:
                if law == "kvkk":
                    return "kişisel verilerin korunması kanunu"
                return law

        cleaned = lower

        phrases_to_remove = [
            "nedir",
            "ne demektir",
            "ne anlama gelir",
            "amacı",
            "amaç",
            "açıkla",
            "özetle",
            "özet",
            "gerekçesi",
            "gerekçe",
            "maddeleri nelerdir",
            "madde listesi",
            "madde ağacı",
            "içindekiler",
            "içinde",
            "bul",
            "ara",
            "?",
        ]

        for phrase in phrases_to_remove:
            cleaned = cleaned.replace(phrase, "")

        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned if cleaned else lower

    def _extract_preferred_mevzuat_id(self, text: str):
        preferred_patterns = [
            r"\[4857\].*?mevzuatId:\s*(\d+)",
            r"\[6698\].*?mevzuatId:\s*(\d+)",
            r"\[5237\].*?mevzuatId:\s*(\d+)",
            r"\[6102\].*?mevzuatId:\s*(\d+)",
            r"\[6098\].*?mevzuatId:\s*(\d+)",
        ]

        for pattern in preferred_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1)

        return self._extract_first_mevzuat_id(text)

    def _extract_first_mevzuat_id(self, text: str):
        match = re.search(r"mevzuatId:\s*(\d+)", text)
        if match:
            return match.group(1)
        return None

    def _extract_gerekce_id(self, text: str):
        match = re.search(r"gerekceId:\s*(\d+)", text)
        if match:
            return match.group(1)
        return None

    def _asks_for_gerekce(self, message: str) -> bool:
        lower = self._normalize_turkish(message)
        return "gerekçe" in lower or "gerekçesi" in lower

    def _asks_for_search_within(self, message: str) -> bool:
        lower = self._normalize_turkish(message)
        keywords = [
            "içinde ara",
            "içinde bul",
            "hangi maddede",
            "hangi maddeler",
            "fazla mesai",
            "fazla çalışma",
            "yıllık izin",
            "kıdem tazminatı",
            "ihbar",
            "işçi çıkarma",
            "fesih",
            "çalışma süresi",
        ]
        return any(keyword in lower for keyword in keywords)

    def _asks_for_tree(self, message: str) -> bool:
        lower = self._normalize_turkish(message)

        if self._asks_for_search_within(message):
            return False

        keywords = [
            "madde ağacı",
            "madde listesi",
            "maddeleri nelerdir",
            "kaç madde",
            "bölümleri",
            "içindekiler",
            "madde başlıkları",
        ]

        return any(keyword in lower for keyword in keywords)

    def _should_fetch_content(self, message: str) -> bool:
        lower = self._normalize_turkish(message)
        keywords = [
            "nedir",
            "amacı",
            "amaç",
            "madde",
            "maddesi",
            "açıkla",
            "özetle",
            "ne anlatıyor",
            "içeriği",
        ]
        return any(keyword in lower for keyword in keywords)

    def _extract_keyword_for_within_search(self, message: str) -> str:
        lower = self._normalize_turkish(message)

        known_keywords = [
            "fazla mesai",
            "fazla çalışma",
            "yıllık izin",
            "kıdem tazminatı",
            "ihbar",
            "fesih",
            "işçi çıkarma",
            "ücret",
            "çalışma süresi",
        ]

        for keyword in known_keywords:
            if keyword in lower:
                return keyword

        return lower