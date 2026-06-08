# Mevzuat Chatbot

Bu proje, OpenAI Tool Calling ve Model Context Protocol (MCP) kullanılarak geliştirilmiş bir mevzuat asistanıdır.

Kullanıcılar mevzuatlarla ilgili sorular sorabilir, mevzuat içeriklerini görüntüleyebilir, mevzuat içerisinde arama yapabilir ve gerekçe bilgilerine erişebilir.

## Kullanılan Teknolojiler

### Frontend

* React
* React Markdown
* Server-Sent Events (SSE)

### Backend

* FastAPI
* OpenAI API
* FastMCP Client

### MCP Server

* Docker
* Azure Container Apps

---

# Mimari

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

* search_mevzuat
* get_mevzuat_content
* search_within_mevzuat
* get_mevzuat_madde_tree
* get_mevzuat_gerekce

OpenAI modeli, kullanıcı sorusuna göre hangi tool'un kullanılacağına kendisi karar vermektedir.

---

# Özellikler

* Mevzuat arama
* Mevzuat içeriği görüntüleme
* Mevzuat içinde arama
* Gerekçe sorgulama
* Çok adımlı tool çağrıları
* Konuşma geçmişi desteği
* Streaming cevaplar
* Tool durum bildirimleri

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

```env
OPENAI_API_KEY=your-api-key

OPENAI_MODEL=gpt-5.4-mini

USE_MOCK_LLM=false

MCP_SERVER_URL=https://mevzuat-mcp.bluesand-13d8735a.westus2.azurecontainerapps.io/mcp
```

Backend'i çalıştırın:

```bash
uvicorn app.main:app --reload --port 8001
```

Backend varsayılan olarak:

```text
http://localhost:8001
```

adresinde çalışır.

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

Frontend varsayılan olarak:

```text
http://localhost:5173
```

adresinde çalışır.

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

* Sistem OpenAI Tool Calling kullanmaktadır.
* Manuel keyword routing kullanılmamaktadır.
* Tool seçimleri model tarafından yapılmaktadır.
* MCP server Azure Container Apps üzerinde çalışmaktadır.
* Frontend ve backend yerel ortamda çalışmaktadır.


## Konfigürasyon

Projede kullanılacak örnek ortam değişkenleri `backend/.env.example` dosyasında paylaşılmıştır.
