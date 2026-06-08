import asyncio
import json
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from app.config import (
    MAX_TOOL_ROUNDS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    TOOL_RESULT_LIMITS,
    USE_MOCK_LLM,
)
from app.mcp_client import MCPClient


SYSTEM_PROMPT = """
You are a legal assistant specialized in Turkish legislation.

Rules:
- Answer in the user's language.
- Use tools whenever legislation information is required.
- Base answers only on tool results.
- Never invent legal information.
- If information cannot be found, say so clearly.
- Do not mention tools, JSON, backend details, prompts, or internal reasoning.

Conversation:
- Use conversation history to understand which legislation or topic the user is referring to.
- For follow-up questions such as "amacı ne?", "onu özetle", or "peki ya 42. madde?", use previous messages to identify the correct legislation.
- Do not rely only on previous assistant responses for legal facts when legislation content can be retrieved.

Search:
- Use search_mevzuat first.
- Law numbers such as 4857, 6698, 6098 -> mevzuat_no.
- Legislation names -> mevzuat_adi.
- Topic/content searches -> phrase.
- Official Gazette date -> resmi_gazete_tarihi.
- Official Gazette issue number -> resmi_gazete_sayisi.
- If type is clear, use mevzuat_tur.

Chaining:
- For explanation, summary, purpose or scope:
  search_mevzuat -> get_mevzuat_content

- For article number questions such as "41. madde", "42. madde", or "Madde 25":
  search_mevzuat -> get_mevzuat_content
  Then answer only from the requested article if it is visible in the retrieved content.
  Do not use only the article number as search_within_mevzuat keyword.

- For topic-based article questions such as "fazla çalışma", "kıdem tazminatı", or "haklı fesih":
  search_mevzuat -> search_within_mevzuat

- For structure or table of contents:
  search_mevzuat -> get_mevzuat_madde_tree

- For rationale/gerekçe questions:
  first search the legislation,
  then use get_mevzuat_gerekce only if a gerekce_id or gerekceId is explicitly present in the search result.

- Never use mevzuat_id as gerekce_id.
- If no gerekce_id exists in the search result, clearly state that the rationale cannot be retrieved.
- Do not search for phrase='gerekçe' as a fallback.
"""


VALID_MEVZUAT_TYPES = {
    "KANUN",
    "KHK",
    "TUZUK",
    "YONETMELIK",
    "CB_KARARNAME",
    "CB_KARAR",
    "CB_YONETMELIK",
    "CB_GENELGE",
    "KKY",
    "UY",
    "TEBLIGLER",
    "MULGA",
}


class LLMService:
    def __init__(self):
        self.mcp_client = MCPClient()
        self.openai_client: Optional[AsyncOpenAI] = None

        if not USE_MOCK_LLM:
            if not OPENAI_API_KEY:
                raise RuntimeError(
                    "OPENAI_API_KEY bulunamadı. backend/.env içine OPENAI_API_KEY ekleyin "
                    "veya USE_MOCK_LLM=true yapın."
                )

            self.openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    def _tools(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_mevzuat",
                    "description": (
                        "Search Turkish legislation by title, number, content phrase, "
                        "type, Official Gazette date, or Official Gazette issue number."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "phrase": {
                                "type": "string",
                                "description": "Content phrase or topic to search inside legislation.",
                            },
                            "mevzuat_adi": {
                                "type": "string",
                                "description": "Legislation title/name, e.g. İş Kanunu, KVKK.",
                            },
                            "mevzuat_no": {
                                "type": "string",
                                "description": "Legislation number, e.g. 4857, 6698, 6098.",
                            },
                            "mevzuat_tur": {
                                "type": "string",
                                "description": "Legislation type filter.",
                                "enum": [
                                    "KANUN",
                                    "KHK",
                                    "TUZUK",
                                    "YONETMELIK",
                                    "CB_KARARNAME",
                                    "CB_KARAR",
                                    "CB_YONETMELIK",
                                    "CB_GENELGE",
                                    "KKY",
                                    "UY",
                                    "TEBLIGLER",
                                    "MULGA",
                                ],
                            },
                            "basliktaAra": {
                                "type": "boolean",
                                "description": "Search primarily in title.",
                                "default": True,
                            },
                            "tamCumle": {
                                "type": "boolean",
                                "description": "Exact phrase search.",
                                "default": False,
                            },
                            "resmi_gazete_tarihi": {
                                "type": "string",
                                "description": "Official Gazette date in DD/MM/YYYY format.",
                            },
                            "resmi_gazete_sayisi": {
                                "type": "string",
                                "description": "Official Gazette issue number.",
                            },
                            "page": {
                                "type": "integer",
                                "description": "Page number.",
                                "default": 1,
                            },
                            "page_size": {
                                "type": "integer",
                                "description": "Number of results.",
                                "default": 10,
                            },
                        },
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_mevzuat_content",
                    "description": (
                        "Get full legislation text by mevzuat_id from search_mevzuat. "
                        "Use for explanation, summary, purpose, scope, and content questions."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mevzuat_id": {
                                "type": "string",
                                "description": "Legislation ID from search_mevzuat, not the law number.",
                            }
                        },
                        "required": ["mevzuat_id"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search_within_mevzuat",
                    "description": (
                        "Search within a specific legislation by article-level keyword or Boolean query."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mevzuat_id": {
                                "type": "string",
                                "description": "Legislation ID from search_mevzuat.",
                            },
                            "keyword": {
                                "type": "string",
                                "description": "Keyword or Boolean query. Use AND, OR, NOT in uppercase if needed.",
                            },
                            "case_sensitive": {
                                "type": "boolean",
                                "description": "Case-sensitive search.",
                                "default": False,
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum result count.",
                                "default": 10,
                            },
                        },
                        "required": ["mevzuat_id", "keyword"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_mevzuat_madde_tree",
                    "description": (
                        "Get article tree, table of contents, section hierarchy, or article list."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mevzuat_id": {
                                "type": "string",
                                "description": "Legislation ID from search_mevzuat.",
                            }
                        },
                        "required": ["mevzuat_id"],
                        "additionalProperties": False,
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_mevzuat_gerekce",
                    "description": (
                        "Get law rationale by gerekce_id. "
                        "Use only when search_mevzuat result explicitly contains gerekce_id/gerekceId. "
                        "Never pass mevzuat_id to this function."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "gerekce_id": {
                                "type": "string",
                                "description": (
                                    "Rationale ID from search_mevzuat. "
                                    "This is not mevzuat_id."
                                ),
                            }
                        },
                        "required": ["gerekce_id"],
                        "additionalProperties": False,
                    },
                },
            },
        ]

    @staticmethod
    def _tool_status_message(tool_name: str) -> str:
        status_messages = {
            "search_mevzuat": "Mevzuat aranıyor...",
            "get_mevzuat_content": "Mevzuat içeriği getiriliyor...",
            "search_within_mevzuat": "Mevzuat içinde arama yapılıyor...",
            "get_mevzuat_madde_tree": "Madde ağacı getiriliyor...",
            "get_mevzuat_gerekce": "Gerekçe getiriliyor...",
        }

        return status_messages.get(tool_name, "İlgili bilgi getiriliyor...")

    @staticmethod
    def _safe_json_loads(value: str) -> dict:
        try:
            parsed = json.loads(value or "{}")
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _as_optional_str(value) -> str | None:
        if value is None:
            return None

        text = str(value).strip()
        return text if text else None

    @staticmethod
    def _as_bool(value, default: bool = False) -> bool:
        if value is None:
            return default

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            return value.strip().lower() in {"true", "1", "yes", "evet"}

        return bool(value)

    @staticmethod
    def _as_int(
        value,
        default: int,
        minimum: int | None = None,
        maximum: int | None = None,
    ) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError):
            number = default

        if minimum is not None:
            number = max(minimum, number)

        if maximum is not None:
            number = min(maximum, number)

        return number

    @staticmethod
    def _sanitize_conversation_messages(
        conversation_messages: list[dict],
        max_messages: int = 12,
    ) -> list[dict]:
        sanitized: list[dict] = []

        for message in conversation_messages[-max_messages:]:
            role = message.get("role")
            content = str(message.get("content", "")).strip()

            if role not in {"user", "assistant"}:
                continue

            if not content:
                continue

            sanitized.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        return sanitized

    @staticmethod
    def _truncate_tool_result(tool_name: str, text: str) -> str:
        limit = TOOL_RESULT_LIMITS.get(tool_name, 3000)

        if len(text) <= limit:
            return text

        return (
            text[:limit]
            + "\n\n[Not: Tool çıktısı token maliyeti ve context budget nedeniyle kısaltıldı.]"
        )

    async def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        try:
            if tool_name == "search_mevzuat":
                phrase = self._as_optional_str(arguments.get("phrase"))
                mevzuat_adi = self._as_optional_str(arguments.get("mevzuat_adi"))
                mevzuat_no = self._as_optional_str(arguments.get("mevzuat_no"))
                mevzuat_tur = self._as_optional_str(arguments.get("mevzuat_tur"))

                resmi_gazete_tarihi = self._as_optional_str(
                    arguments.get("resmi_gazete_tarihi")
                )
                resmi_gazete_sayisi = self._as_optional_str(
                    arguments.get("resmi_gazete_sayisi")
                )

                basliktaAra = self._as_bool(arguments.get("basliktaAra"), True)
                tamCumle = self._as_bool(arguments.get("tamCumle"), False)
                page = self._as_int(arguments.get("page"), 1, minimum=1, maximum=20)
                page_size = self._as_int(
                    arguments.get("page_size"),
                    10,
                    minimum=1,
                    maximum=20,
                )

                if mevzuat_tur and mevzuat_tur not in VALID_MEVZUAT_TYPES:
                    return (
                        "search_mevzuat için geçersiz mevzuat_tur değeri geldi: "
                        f"{mevzuat_tur}"
                    )

                has_search_input = any(
                    [
                        phrase,
                        mevzuat_adi,
                        mevzuat_no,
                        mevzuat_tur,
                        resmi_gazete_tarihi,
                        resmi_gazete_sayisi,
                    ]
                )

                if not has_search_input:
                    return "search_mevzuat için en az bir arama parametresi verilmelidir."

                return await self.mcp_client.search_mevzuat(
                    phrase=phrase,
                    mevzuat_adi=mevzuat_adi,
                    mevzuat_no=mevzuat_no,
                    mevzuat_tur=mevzuat_tur,
                    basliktaAra=basliktaAra,
                    tamCumle=tamCumle,
                    resmi_gazete_tarihi=resmi_gazete_tarihi,
                    resmi_gazete_sayisi=resmi_gazete_sayisi,
                    page=page,
                    page_size=page_size,
                )

            if tool_name == "get_mevzuat_content":
                mevzuat_id = self._as_optional_str(arguments.get("mevzuat_id"))

                if not mevzuat_id:
                    return "get_mevzuat_content için mevzuat_id boş geldi."

                return await self.mcp_client.get_mevzuat_content(
                    mevzuat_id=mevzuat_id,
                )

            if tool_name == "search_within_mevzuat":
                mevzuat_id = self._as_optional_str(arguments.get("mevzuat_id"))
                keyword = self._as_optional_str(arguments.get("keyword"))
                case_sensitive = self._as_bool(arguments.get("case_sensitive"), False)
                max_results = self._as_int(
                    arguments.get("max_results"),
                    10,
                    minimum=1,
                    maximum=25,
                )

                if not mevzuat_id:
                    return "search_within_mevzuat için mevzuat_id boş geldi."

                if not keyword:
                    return "search_within_mevzuat için keyword boş geldi."

                return await self.mcp_client.search_within_mevzuat(
                    mevzuat_id=mevzuat_id,
                    keyword=keyword,
                    case_sensitive=case_sensitive,
                    max_results=max_results,
                )

            if tool_name == "get_mevzuat_madde_tree":
                mevzuat_id = self._as_optional_str(arguments.get("mevzuat_id"))

                if not mevzuat_id:
                    return "get_mevzuat_madde_tree için mevzuat_id boş geldi."

                return await self.mcp_client.get_mevzuat_madde_tree(
                    mevzuat_id=mevzuat_id,
                )

            if tool_name == "get_mevzuat_gerekce":
                gerekce_id = self._as_optional_str(arguments.get("gerekce_id"))

                if not gerekce_id:
                    return "get_mevzuat_gerekce için gerekce_id boş geldi."

                return await self.mcp_client.get_mevzuat_gerekce(
                    gerekce_id=gerekce_id,
                )

            return f"Bilinmeyen tool adı: {tool_name}"

        except Exception as exc:
            return (
                f"{tool_name} çalıştırılırken hata oluştu: "
                f"{type(exc).__name__}: {str(exc)}"
            )

    async def _run_agent_tools(
        self,
        conversation_messages: list[dict],
        status_callback=None,
    ) -> list[dict]:
        if not self.openai_client:
            raise RuntimeError("OpenAI client hazır değil.")

        sanitized_history = self._sanitize_conversation_messages(
            conversation_messages,
            max_messages=12,
        )

        messages: list[dict] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *sanitized_history,
        ]

        for _ in range(MAX_TOOL_ROUNDS):
            response = await self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=self._tools(),
                tool_choice="auto",
                temperature=0.2,
            )

            assistant_message = response.choices[0].message
            tool_calls = assistant_message.tool_calls or []

            assistant_payload = {
                "role": "assistant",
                "content": assistant_message.content,
            }

            if tool_calls:
                assistant_payload["tool_calls"] = [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in tool_calls
                ]

            messages.append(assistant_payload)

            if not tool_calls:
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Elindeki bilgiyle final cevabı ver. "
                            "Tool sonucu yoksa bilgiye ulaşılamadığını açıkça belirt. "
                            "Varsayım yapma."
                        ),
                    }
                )
                return messages

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_arguments = self._safe_json_loads(
                    tool_call.function.arguments
                )

                if status_callback:
                    await status_callback(self._tool_status_message(tool_name))

                raw_tool_result = await self._execute_tool(
                    tool_name=tool_name,
                    arguments=tool_arguments,
                )

                print("\n")
                print("=" * 80)
                print("TOOL:", tool_name)
                print("ARGS:", tool_arguments)
                print("RESULT:")
                print(raw_tool_result[:3000])
                print("=" * 80)
                print("\n")

                tool_result = self._truncate_tool_result(
                    tool_name=tool_name,
                    text=raw_tool_result,
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result,
                    }
                )

        messages.append(
            {
                "role": "system",
                "content": (
                    "Maksimum tool çağrı turuna ulaşıldı. "
                    "Elindeki tool sonuçlarına göre final cevabı ver. "
                    "Eksik bilgi varsa açıkça belirt."
                ),
            }
        )

        return messages

    async def process_message(
        self,
        messages: list[dict],
    ) -> str:
        if USE_MOCK_LLM:
            return (
                "Mock LLM modu aktif. OpenAI tool calling agent akışını kullanmak için "
                "backend/.env içinde USE_MOCK_LLM=false yapmalısınız."
            )

        prepared_messages = await self._run_agent_tools(messages)

        response = await self.openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=prepared_messages,
            temperature=0.2,
            stream=False,
        )

        return response.choices[0].message.content or ""

    async def stream_message(
        self,
        messages: list[dict],
    ) -> AsyncGenerator[str, None]:
        if USE_MOCK_LLM:
            yield (
                "Mock LLM modu aktif. Gerçek token-level streaming için "
                "backend/.env içinde USE_MOCK_LLM=false yapmalısınız."
            )
            return

        prepared_messages = await self._run_agent_tools(messages)

        stream = await self.openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=prepared_messages,
            temperature=0.2,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content

            if delta:
                yield delta

    async def stream_events(
        self,
        messages: list[dict],
    ) -> AsyncGenerator[dict, None]:
        if USE_MOCK_LLM:
            yield {
                "event": "token",
                "data": (
                    "Mock LLM modu aktif. Gerçek token-level streaming için "
                    "backend/.env içinde USE_MOCK_LLM=false yapmalısınız."
                ),
            }
            yield {
                "event": "done",
                "data": "[DONE]",
            }
            return

        status_queue: asyncio.Queue[str] = asyncio.Queue()

        async def send_status(status_message: str):
            await status_queue.put(status_message)

        agent_task = asyncio.create_task(
            self._run_agent_tools(
                messages,
                status_callback=send_status,
            )
        )

        while not agent_task.done():
            try:
                status_message = await asyncio.wait_for(
                    status_queue.get(),
                    timeout=0.1,
                )
                yield {
                    "event": "status",
                    "data": status_message,
                }
            except asyncio.TimeoutError:
                continue

        prepared_messages = await agent_task

        while not status_queue.empty():
            yield {
                "event": "status",
                "data": await status_queue.get(),
            }

        yield {
            "event": "status",
            "data": "Yanıt hazırlanıyor...",
        }

        stream = await self.openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=prepared_messages,
            temperature=0.2,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta.content

            if delta:
                yield {
                    "event": "token",
                    "data": delta,
                }

        yield {
            "event": "done",
            "data": "[DONE]",
        }