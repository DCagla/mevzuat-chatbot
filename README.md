# Mevzuat MCP Chatbot

Bu proje, MCP (Model Context Protocol) tabanlı bir mevzuat sunucusu kullanarak mevzuat sorgularına cevap verebilen bir chatbot uygulamasıdır.

## Proje Mimarisi

Proje aşağıdaki bileşenlerden oluşmaktadır:

* MCP Server
* Python FastAPI Backend
* React Frontend
* OpenAI Entegrasyonu
* Streaming Yanıt Desteği

İstek akışı:

Frontend → Backend → MCP Server → OpenAI → Kullanıcı

## MCP Server

Case study kapsamında verilen aşağıdaki repository kullanılmıştır:

https://github.com/saidsurucu/mevzuat-mcp

Repository Dockerize edilmiş ve Azure Container Apps ortamına deploy edilmiştir.

MCP Endpoint:

https://mevzuat-mcp.bluesand-13d8735a.westus2.azurecontainerapps.io/mcp

Backend aşağıdaki MCP tool'larını kullanmaktadır:

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

Backend'i çalıştırın:

```bash
uvicorn app.main:app --reload --port 8001
```

Health endpoint:

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

Frontend'i çalıştırın:

```bash
npm run dev
```

Frontend URL:

```text
http://localhost:5173
```

## API Endpointleri

Normal Chat:

```text
POST /chat
```

Streaming Chat:

```text
POST /chat/stream
```

## Test Edilen MCP Tool'ları

* search_mevzuat
* get_mevzuat_content
* search_within_mevzuat
* get_mevzuat_madde_tree
* get_mevzuat_gerekce

## Notlar

* MCP Server Azure Container Apps üzerinde çalışmaktadır.
* Backend ve frontend lokal ortamda çalışmaktadır.
* Streaming yanıt desteği bulunmaktadır.
* OpenAI yalnızca MCP tool çıktıları üzerinden cevap üretmektedir.

## Konfigürasyon

Projenin çalıştırılması için gerekli ortam değişkenleri `backend/.env.example` dosyasında örnek olarak verilmiştir.
