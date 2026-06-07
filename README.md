\# Mevzuat MCP Chatbot



Bu proje, MCP (Model Context Protocol) tabanlı bir mevzuat sunucusu kullanarak mevzuat sorgularına cevap verebilen bir chatbot uygulamasıdır.



\## Proje Mimarisi



Proje aşağıdaki bileşenlerden oluşmaktadır:



\* MCP Server

\* Python FastAPI Backend

\* React Frontend

\* OpenAI Entegrasyonu

\* Streaming Yanıt Desteği



```text

React Frontend

&#x20;     |

&#x20;     v

FastAPI Backend

&#x20;     |

&#x20;     v

MCP Server (Azure Container Apps)

&#x20;     |

&#x20;     v

Mevzuat Tool'ları

&#x20;     |

&#x20;     v

OpenAI

```



\## MCP Server



Case study kapsamında verilen aşağıdaki repository kullanılmıştır:



https://github.com/saidsurucu/mevzuat-mcp



Repository Dockerize edilmiş ve Azure Container Apps ortamına deploy edilmiştir.



MCP Endpoint:



```text

https://mevzuat-mcp.bluesand-13d8735a.westus2.azurecontainerapps.io/mcp

```



Backend aşağıdaki MCP tool'larını kullanmaktadır:



\* search\_mevzuat

\* get\_mevzuat\_content

\* search\_within\_mevzuat

\* get\_mevzuat\_madde\_tree

\* get\_mevzuat\_gerekce



\## Backend Kurulumu



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

OPENAI\_API\_KEY=your-openai-api-key

OPENAI\_MODEL=gpt-5.4-mini

USE\_MOCK\_LLM=false

MCP\_SERVER\_URL=https://mevzuat-mcp.bluesand-13d8735a.westus2.azurecontainerapps.io/mcp

```



Backend'i çalıştırın:



```bash

uvicorn app.main:app --reload --port 8001

```



Health endpoint:



```text

http://localhost:8001/health

```



\## Frontend Kurulumu



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



\## API Endpointleri



Normal Chat:



```text

POST /chat

```



Streaming Chat:



```text

POST /chat/stream

```



\## Test Edilen Sorular



\* İş Kanunu nedir?

\* İş Kanunu maddeleri nelerdir?

\* İş Kanunu içinde fazla çalışma ile ilgili maddeleri bul

\* Türk Ceza Kanunu gerekçesi nedir?



\## Test Edilen MCP Tool'ları



\* search\_mevzuat

\* get\_mevzuat\_content

\* search\_within\_mevzuat

\* get\_mevzuat\_madde\_tree

\* get\_mevzuat\_gerekce



\## Notlar



\* MCP Server Azure Container Apps üzerinde çalışmaktadır.

\* Backend ve frontend lokal ortamda çalışmaktadır.

\* Streaming yanıt desteği bulunmaktadır.

\* OpenAI yalnızca MCP tool çıktıları üzerinden cevap üretmektedir.



\## Konfigürasyon



Projenin çalıştırılması için gerekli ortam değişkenleri `backend/.env.example` dosyasında örnek olarak verilmiştir.



