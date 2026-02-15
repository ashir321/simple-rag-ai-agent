import React, { useState } from "react";

// Get backend URL from environment variable or use default
// Empty string means use relative URLs (for k8s with nginx proxy)
// If not set, default to localhost for development
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL !== undefined 
  ? import.meta.env.VITE_BACKEND_URL 
  : "http://localhost:8000";

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

      if (!res.ok) {
        // Handle HTTP error responses
        let errorMessage = "Sorry, I encountered an error. Please try again.";
        try {
          const errorData = await res.json();
          if (errorData.detail) {
            errorMessage = `Error: ${errorData.detail}`;
          }
        } catch (e) {
          // If response is not JSON, use status text
          errorMessage = `Server error (${res.status}): ${res.statusText}`;
        }
        setMsgs((m) => [...m, { role: "bot", text: errorMessage }]);
        return;
      }

      const data = await res.json();
      if (data.answer) {
        setMsgs((m) => [...m, { role: "bot", text: data.answer }]);
      } else {
        setMsgs((m) => [...m, { role: "bot", text: "Sorry, I didn't receive a valid response." }]);
      }
    } catch (err) {
      // Network errors or other exceptions
      setMsgs((m) => [...m, { 
        role: "bot", 
        text: "Unable to contact the server. Please check your connection and try again." 
      }]);
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