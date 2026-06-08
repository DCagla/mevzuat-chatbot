import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

const API_BASE_URL = "http://localhost:8001";

const INITIAL_ASSISTANT_MESSAGE = {
  role: "assistant",
  content: "Merhaba, mevzuat hakkında bir soru sorabilirsiniz.",
};

function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([INITIAL_ASSISTANT_MESSAGE]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, status]);

  const appendToLastAssistantMessage = (chunk) => {
    setMessages((prev) => {
      const updated = [...prev];
      const lastIndex = updated.length - 1;

      updated[lastIndex] = {
        ...updated[lastIndex],
        content: updated[lastIndex].content + chunk,
      };

      return updated;
    });
  };

  const replaceLastAssistantMessage = (content) => {
    setMessages((prev) => {
      const updated = [...prev];
      const lastIndex = updated.length - 1;

      updated[lastIndex] = {
        role: "assistant",
        content,
      };

      return updated;
    });
  };

  const getConversationPayload = (nextUserMessage) => {
    return messages
      .filter((message) => message.content.trim())
      .concat({
        role: "user",
        content: nextUserMessage,
      })
      .slice(-12);
  };

  const parseSSEBlock = (block) => {
    const lines = block.split("\n");
    let eventName = "message";
    let data = "";

    for (const line of lines) {
      if (line.startsWith("event:")) {
        eventName = line.replace("event:", "").trim();
      }

      if (line.startsWith("data:")) {
        data += line.replace("data:", "").trim();
      }
    }

    if (!data) return;

    const parsedData = JSON.parse(data);

    if (eventName === "status") {
      setStatus(parsedData);
    }

    if (eventName === "token") {
      setStatus("");
      appendToLastAssistantMessage(parsedData);
    }

    if (eventName === "error") {
      setStatus("");
      replaceLastAssistantMessage(parsedData);
    }

    if (eventName === "done") {
      setStatus("");
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const question = input.trim();
    const conversationPayload = getConversationPayload(question);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "" },
    ]);

    setInput("");
    setLoading(true);
    setStatus("Yanıt hazırlanıyor...");

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify({
          messages: conversationPayload,
        }),
      });

      if (!response.ok) {
        throw new Error(`Backend HTTP error: ${response.status}`);
      }

      if (!response.body) {
        throw new Error("Streaming response body bulunamadı.");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() || "";

        for (const block of blocks) {
          parseSSEBlock(block);
        }
      }

      if (buffer.trim()) {
        parseSSEBlock(buffer);
      }
    } catch (error) {
      console.error(error);

      replaceLastAssistantMessage(
        "Bir hata oluştu. Lütfen backend'in çalıştığını, OPENAI_API_KEY değerini ve MCP server bağlantısını kontrol edin."
      );
    } finally {
      setStatus("");
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <main className="app-shell">
      <section className="chat-container">
        <header className="chat-header">
          <h1>Mevzuat Chatbot</h1>
          <p>Mevzuat asistanı</p>
        </header>

        <section className="messages-panel">
          {messages.map((message, index) => {
            const isUser = message.role === "user";
            const isLast = index === messages.length - 1;
            const showTyping = loading && isLast && !message.content && !isUser;

            return (
              <article
                key={`${message.role}-${index}`}
                className={`message-row ${
                  isUser ? "message-row-user" : "message-row-bot"
                }`}
              >
                <div
                  className={`message-bubble ${
                    isUser ? "user-bubble" : "bot-bubble"
                  }`}
                >
                  <div className="message-label">
                    {isUser ? "Siz" : "Mevzuat Bot"}
                  </div>

                  <div className="message-content">
                    {showTyping ? (
                      <span className="typing-indicator">
                        {status || "Yanıt hazırlanıyor"}
                        <span>.</span>
                        <span>.</span>
                        <span>.</span>
                      </span>
                    ) : (
                      <ReactMarkdown>{message.content}</ReactMarkdown>
                    )}
                  </div>
                </div>
              </article>
            );
          })}

          <div ref={messagesEndRef} />
        </section>

        <footer className="composer">
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Örn: İş Kanunu nedir?"
            rows={2}
            disabled={loading}
          />

          <button onClick={sendMessage} disabled={loading || !input.trim()}>
            {loading ? "Yanıtlanıyor" : "Gönder"}
          </button>
        </footer>
      </section>
    </main>
  );
}

export default App;