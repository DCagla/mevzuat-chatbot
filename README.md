# Mevzuat MCP Chatbot

Bu proje, MCP (Model Context Protocol) tabanlı bir mevzuat chatbot uygulamasıdır.

Sistem; React tabanlı frontend, FastAPI tabanlı backend, Azure Container Apps üzerinde çalışan bir MCP Server ve OpenAI entegrasyonundan oluşmaktadır.

## Kullanılan Teknolojiler

* React
* FastAPI
* OpenAI
* MCP (Model Context Protocol)
* Docker
* Azure Container Apps

## Mimari

```text
Kullanıcı
    │
    ▼
React Frontend
    │
    ▼
FastAPI Backend
    │
    ▼
MCP Server
    │
    ▼
Mevzuat Verisi
    │
    ▼
OpenAI
    │
    ▼
Yanıt
```

## MCP Server

Case study kapsamında verilen aşağıdaki repository kullanılmıştır:

https://github.com/saidsurucu/mevzuat-mcp

Repository Dockerize edilmiş ve Azure Container Apps ortamına deploy edilmiştir.

MCP Endpoint:

```text
https://mevzuat-mcp.bluesand-13d8735a.westus2.azurecontainerapps.io/mcp
```

Kullanılan MCP tool'ları:

* search_mevzuat
* get_mevzuat_content
* search_within_mevzuat
* get_mevzuat_madde_tree
* get_mevzuat_gerekce

## Backend Kurulumu

Backend klasörüne geçin:

```bash
cd backend
```

Gerekli paketleri yükleyin:

```bash
pip install -r requirements.txt
```

`backend/.env` dosyasını oluşturun:

```env
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-5.4-mini
USE_MOCK_LLM=false
MCP_SERVER_URL=https://mevzuat-mcp.bluesand-13d8735a.westus2.azurecontainerapps.io/mcp
```

Backend uygulamasını çalıştırın:

```bash
uvicorn app.main:app --reload --port 8001
```

Health Check:

```text
http://localhost:8001/health
```

## Frontend Kurulumu

Frontend klasörüne geçin:

```bash
cd frontend
```

Bağımlılıkları yükleyin:

```bash
npm install
```

Frontend uygulamasını çalıştırın:

```bash
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

## API Endpointleri

| Endpoint     | Method |
| ------------ | ------ |
| /chat        | POST   |
| /chat/stream | POST   |

## Konfigürasyon

Projede kullanılacak örnek ortam değişkenleri `backend/.env.example` dosyasında paylaşılmıştır.
