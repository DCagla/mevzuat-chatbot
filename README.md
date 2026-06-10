# Mevzuat Chatbot

Bu proje, OpenAI Tool Calling ve Model Context Protocol (MCP) kullanılarak geliştirilmiş bir mevzuat asistanıdır.

Kullanıcılar mevzuatlarla ilgili sorular sorabilir, mevzuat içeriklerini görüntüleyebilir, mevzuat içerisinde arama yapabilir ve gerekçe bilgilerine erişebilir.

## Kullanılan Teknolojiler

### Frontend

- React
- React Markdown
- Server-Sent Events (SSE)

### Backend

- FastAPI
- OpenAI API
- FastMCP Client

### MCP Server

- Docker
- Azure Container Apps

---

# Mimari

```
Kullanıcı
    │
    ▼
React Frontend
    │
    ▼
FastAPI Backend
    │
    ▼
OpenAI Tool Calling
    │
    ▼
MCP Server
    │
    ▼
Mevzuat Verisi
```

Frontend ve backend yerel ortamda çalışmaktadır.

MCP server Azure Container Apps üzerinde yayınlanmıştır ve backend tarafından uzaktan kullanılmaktadır.

---

# Kullanılan MCP Tool'ları

Projede aşağıdaki MCP tool'ları kullanılmaktadır:

- search_mevzuat
- get_mevzuat_content
- search_within_mevzuat
- get_mevzuat_madde_tree
- get_mevzuat_gerekce

OpenAI modeli, kullanıcı sorusuna göre hangi tool'un kullanılacağına kendisi karar vermektedir.
Birden fazla tool gerektiğinde model çok adımlı (multi-step) tool çağrıları gerçekleştirebilir.

---

# Özellikler

- Mevzuat arama
- Mevzuat içeriği görüntüleme
- Mevzuat içinde arama
- Gerekçe sorgulama
- Çok adımlı tool çağrıları
- Konuşma geçmişi desteği
- Streaming cevaplar
- Tool durum bildirimleri
- OpenAI Tool Calling
- Conversation Context Management

---

# MCP Server Deployment

MCP server, Docker ile containerize edilip Azure Container Apps üzerinde deploy edilmiştir.

## 1. Docker Image Oluşturma

MCP server klasörüne geçin ve image'ı oluşturun:

```bash
cd mcp-server
docker build -t mevzuat-mcp .
```

Lokal ortamda test etmek için container çalıştırın:

```bash
docker run --rm -p 8000:8000 mevzuat-mcp
```

Health endpoint'i kontrol edin:

```bash
curl http://localhost:8000/health
```

Beklenen çıktı:

```json
{
  "status": "healthy",
  "service": "Mevzuat MCP Server",
  "version": "0.1.0"
}
```

## 2. Azure Container Registry'e Push Etme

Azure CLI ile giriş yapın:

```bash
az login
```

Image'ı ACR için tag'leyin:

```bash
docker tag mevzuat-mcp:latest ca17532f4a42acr.azurecr.io/mevzuat-mcp:latest
```

ACR'a giriş yapın ve image'ı push edin:

```bash
az acr login --name ca17532f4a42acr
docker push ca17532f4a42acr.azurecr.io/mevzuat-mcp:latest
```

## 3. Azure Container App'i Güncelleme

Mevcut Container App yeni image ile güncellendi:

```bash
az containerapp update \
  --name mevzuat-mcp \
  --resource-group case-study-dilara-cagla-banko \
  --image ca17532f4a42acr.azurecr.io/mevzuat-mcp:latest
```

## 4. Deploy Sonrası Kontrol

Container App URL'ini alın:

```bash
az containerapp show \
  --name mevzuat-mcp \
  --resource-group case-study-dilara-cagla-banko \
  --query "properties.configuration.ingress.fqdn" \
  --output tsv
```

Health endpoint'i kontrol edin:

```bash
curl https://mevzuat-mcp.bluesand-13d8735a.westus2.azurecontainerapps.io/health
```

## 5. Backend Konfigürasyonu

Deploy sonrası MCP server URL'i backend `.env` dosyasına girildi:

```env
MCP_SERVER_URL=https://mevzuat-mcp.bluesand-13d8735a.westus2.azurecontainerapps.io/mcp
```

---

# Backend Kurulumu

Backend klasörüne geçin:

```bash
cd backend
```

Bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

`.env` dosyası oluşturun:

```
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-5.4-mini
USE_MOCK_LLM=false
MCP_SERVER_URL=https://mevzuat-mcp.bluesand-13d8735a.westus2.azurecontainerapps.io/mcp
```

Backend'i çalıştırın:

```bash
uvicorn app.main:app --reload --port 8001
```

Backend varsayılan olarak `http://localhost:8001` adresinde çalışır.

---

# Frontend Kurulumu

Frontend klasörüne geçin:

```bash
cd frontend
```

Bağımlılıkları yükleyin:

```bash
npm install
```

Frontend'i başlatın:

```bash
npm run dev
```

Frontend varsayılan olarak `http://localhost:5173` adresinde çalışır.

---

# API

## POST /chat

Streaming olmayan cevap üretir.

## POST /chat/stream

Streaming cevap üretir.

Konuşma geçmişi aşağıdaki formatta gönderilir:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "4857 sayılı İş Kanunu nedir?"
    }
  ]
}
```

---

# Notlar

- Sistem OpenAI Tool Calling kullanmaktadır.
- Manuel keyword routing kullanılmamaktadır.
- Tool seçimleri model tarafından yapılmaktadır.
- MCP server Azure Container Apps üzerinde çalışmaktadır.
- Frontend ve backend yerel ortamda çalışmaktadır.

## Konfigürasyon

Projede kullanılacak örnek ortam değişkenleri `backend/.env.example` dosyasında paylaşılmıştır.
