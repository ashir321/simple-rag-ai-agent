import React, { useState } from "react";

// Get backend URL from environment variable or use default
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

export default function ChatWidget() {
  const [msgs, setMsgs] = useState([{ role: "bot", text: "Hi! Ask me about your policy." }]);
  const [text, setText] = useState("");

  async function send() {
    const msg = text.trim();
    if (!msg) return;

    setMsgs((m) => [...m, { role: "user", text: msg }]);
    setText("");

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });
      const data = await res.json();
      setMsgs((m) => [...m, { role: "bot", text: data.answer }]);
    } catch (err) {
      setMsgs((m) => [...m, { role: "bot", text: "Error contacting server." }]);
    }
  }

  return (
    <div className="chat-widget">
      <div className="messages" role="log" aria-live="polite">
        {msgs.map((m, i) => (
          <div key={i} className={"msg " + (m.role === "user" ? "msg-user" : "msg-bot") }>
            <div className="msg-text">{m.text}</div>
          </div>
        ))}
      </div>

      <div className="input-row">
        <input
          className="chat-input"
          placeholder="Ask about your policy..."
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") send(); }}
        />
        <button className="chat-send" onClick={send}>Send</button>
      </div>
    </div>
  );
}