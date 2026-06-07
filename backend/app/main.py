import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

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


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Mevzuat Chatbot Backend"
    }


@app.get("/test-content")
async def test_content():
    result = await mcp_client.get_mevzuat_content("103054")
    return {"result": str(result)}


@app.get("/test-tree")
async def test_tree():
    result = await mcp_client.get_mevzuat_madde_tree("103054")
    return {"result": str(result)}


@app.get("/test-search-within")
async def test_search_within():
    result = await mcp_client.search_within_mevzuat(
        "103054",
        "fazla çalışma"
    )
    return {"result": str(result)}


@app.get("/test-gerekce")
async def test_gerekce():
    search_result = await mcp_client.search_mevzuat("iş kanunu")
    return {
        "note": "Gerekçe tool'u için search_mevzuat sonucunda gerekce_id varsa kullanılmalıdır.",
        "search_result": str(search_result)
    }


@app.post("/chat")
async def chat(payload: dict):
    message = payload.get("message", "")
    answer = await llm_service.process_message(message)
    return {"answer": answer}


@app.post("/chat/stream")
async def chat_stream(payload: dict):
    message = payload.get("message", "")

    async def generate():
        answer = await llm_service.process_message(message)

        for char in answer:
            yield char
            await asyncio.sleep(0.003)

    return StreamingResponse(generate(), media_type="text/plain")