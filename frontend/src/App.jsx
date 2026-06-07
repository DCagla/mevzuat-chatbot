import { useState } from "react";

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "Merhaba, mevzuat hakkında bir soru sorabilirsiniz.",
    },
  ]);
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();

    const userMessage = {
      role: "user",
      content: question,
    };

    const assistantMessage = {
      role: "assistant",
      content: "",
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://localhost:8001/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: question,
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);

        setMessages((prev) => {
          const updated = [...prev];
          const lastIndex = updated.length - 1;

          updated[lastIndex] = {
            ...updated[lastIndex],
            content: updated[lastIndex].content + chunk,
          };

          return updated;
        });
      }
    } catch (error) {
      console.error(error);

      setMessages((prev) => {
        const updated = [...prev];
        const lastIndex = updated.length - 1;

        updated[lastIndex] = {
          role: "assistant",
          content:
            "Bir hata oluştu. Lütfen backend ve MCP server'ın çalıştığını kontrol edin.",
        };

        return updated;
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div
      style={{
        height: "100vh",
        backgroundColor: "#f6f7f9",
        fontFamily: "Arial, sans-serif",
        display: "flex",
        justifyContent: "center",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "900px",
          height: "100vh",
          display: "flex",
          flexDirection: "column",
          backgroundColor: "#ffffff",
          borderLeft: "1px solid #e5e7eb",
          borderRight: "1px solid #e5e7eb",
          overflow: "hidden",
          textAlign: "left",
        }}
      >
        <div
          style={{
            padding: "18px 24px",
            borderBottom: "1px solid #e5e7eb",
            textAlign: "center",
            flexShrink: 0,
          }}
        >
          <h1
            style={{
              margin: 0,
              fontSize: "28px",
              lineHeight: "1.2",
            }}
          >
            Mevzuat Chatbot
          </h1>

          <p
            style={{
              margin: "6px 0 0",
              color: "#6b7280",
              fontSize: "14px",
            }}
          >
            MCP tabanlı mevzuat asistanı
          </p>
        </div>

        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: "24px",
            backgroundColor: "#ffffff",
          }}
        >
          {messages.map((msg, index) => (
            <div
              key={index}
              style={{
                display: "flex",
                justifyContent:
                  msg.role === "user" ? "flex-end" : "flex-start",
                marginBottom: "16px",
                width: "100%",
              }}
            >
              <div
                style={{
                  width: "fit-content",
                  maxWidth: "75%",
                  padding: "14px 16px",
                  borderRadius: "14px",
                  backgroundColor:
                    msg.role === "user" ? "#2563eb" : "#f3f4f6",
                  color: msg.role === "user" ? "#ffffff" : "#111827",
                  whiteSpace: "pre-wrap",
                  textAlign: "left",
                  lineHeight: "1.6",
                  fontSize: "15px",
                  overflowWrap: "break-word",
                  wordBreak: "break-word",
                }}
              >
                <div
                  style={{
                    fontSize: "12px",
                    fontWeight: "bold",
                    marginBottom: "6px",
                    opacity: 0.75,
                    textAlign: "left",
                  }}
                >
                  {msg.role === "user" ? "Siz" : "Mevzuat Bot"}
                </div>

                <div>{msg.content || "Yanıt hazırlanıyor..."}</div>
              </div>
            </div>
          ))}
        </div>

        <div
          style={{
            padding: "16px 24px",
            borderTop: "1px solid #e5e7eb",
            backgroundColor: "#ffffff",
            flexShrink: 0,
          }}
        >
          <div
            style={{
              display: "flex",
              gap: "10px",
              alignItems: "stretch",
            }}
          >
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Örn: İş Kanunu nedir?"
              rows={2}
              disabled={loading}
              style={{
                flex: 1,
                resize: "none",
                padding: "12px",
                borderRadius: "10px",
                border: "1px solid #d1d5db",
                fontSize: "15px",
                fontFamily: "inherit",
                lineHeight: "1.5",
                outline: "none",
                textAlign: "left",
              }}
            />

            <button
              onClick={sendMessage}
              disabled={loading}
              style={{
                padding: "0 22px",
                borderRadius: "10px",
                border: "none",
                backgroundColor: loading ? "#9ca3af" : "#2563eb",
                color: "#ffffff",
                fontSize: "15px",
                cursor: loading ? "not-allowed" : "pointer",
                minWidth: "90px",
              }}
            >
              {loading ? "..." : "Gönder"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;