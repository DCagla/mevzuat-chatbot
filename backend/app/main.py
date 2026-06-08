import json
from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.llm_service import LLMService
from app.mcp_client import MCPClient

app = FastAPI(title="Mevzuat Chatbot Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

llm_service = LLMService()
mcp_client = MCPClient()


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Mevzuat Chatbot Backend",
    }


@app.post("/chat")
async def chat(payload: ChatRequest):
    messages = [message.model_dump() for message in payload.messages]
    answer = await llm_service.process_message(messages)
    return {"answer": answer}


@app.post("/chat/stream")
async def chat_stream(payload: ChatRequest):
    async def generate():
        try:
            messages = [message.model_dump() for message in payload.messages]

            async for event in llm_service.stream_events(messages):
                yield (
                    f"event: {event['event']}\n"
                    f"data: {json.dumps(event['data'])}\n\n"
                )

        except Exception as exc:
            error_message = (
                "Bir hata oluştu. Lütfen backend loglarını, OPENAI_API_KEY değerini "
                f"ve MCP server bağlantısını kontrol edin. Hata: {type(exc).__name__}: {str(exc)}"
            )
            yield f"event: error\ndata: {json.dumps(error_message)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )