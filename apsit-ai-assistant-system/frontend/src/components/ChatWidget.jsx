import React, { useState, useEffect, useRef } from "react";

const BACKEND_URL = "https://apsit-ai-production.up.railway.app";

const QUICK = [
  "Admissions",
  "Placements",
  "Courses",
  "Fees",
  "Facilities",
  "Contact"
];

export default function ChatWidget({ close }) {

  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [language, setLanguage] = useState("auto");

  const chatEndRef = useRef(null);

  // 🔥 Auto scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendQuery = async (q) => {

    const text = q || query;
    if (!text) return;

    // add user message
    setMessages(prev => [...prev, { role: "user", text }]);
    setQuery("");
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          query: text,
          session_id: "apsit",
          language
        })
      });

      const data = await res.json();

      setMessages(prev => [
        ...prev,
        {
          role: "bot",
          text: data.answer,
          images: data.images || [],
          pdfs: data.pdfs || []
        }
      ]);

    } catch (e) {
      setMessages(prev => [
        ...prev,
        { role: "bot", text: "Server error. Try again." }
      ]);
    }

    setLoading(false);
  };

  return (
    <div style={{
      position: "fixed",
      bottom: "90px",
      right: "20px",
      width: "360px",
      background: "#fff",
      borderRadius: "14px",
      boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
      overflow: "hidden",
      zIndex: 9999,
      fontFamily: "Arial"
    }}>

      {/* HEADER */}
      <div style={{
        background: "#d32f2f",
        color: "#fff",
        padding: "12px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center"
      }}>
        <b>APSIT Assistant</b>
        <span style={{ cursor: "pointer" }} onClick={close}>✖</span>
      </div>

      {/* QUICK BUTTONS */}
      <div style={{ padding: "10px" }}>
        {QUICK.map((q, i) => (
          <button
            key={i}
            onClick={() => sendQuery(q)}
            style={{
              margin: "4px",
              padding: "6px 10px",
              borderRadius: "20px",
              border: "1px solid #d32f2f",
              background: "#fff",
              cursor: "pointer",
              fontSize: "12px"
            }}
          >
            {q}
          </button>
        ))}
      </div>

      {/* CHAT AREA */}
      <div style={{
        height: "280px",
        overflowY: "auto",
        padding: "10px",
        background: "#f5f5f5"
      }}>
        {messages.map((m, i) => (
          <div
            key={i}
            style={{
              textAlign: m.role === "user" ? "right" : "left",
              marginBottom: "12px"
            }}
          >
            <div style={{
              display: "inline-block",
              padding: "10px",
              borderRadius: "12px",
              background: m.role === "user" ? "#d32f2f" : "#fff",
              color: m.role === "user" ? "#fff" : "#000",
              maxWidth: "85%",
              whiteSpace: "pre-wrap",
              lineHeight: "1.5",
              fontSize: "14px"
            }}>

              {m.text}

              {/* IMAGES */}
              {m.images && m.images.map((img, idx) => (
                <div key={idx} style={{ marginTop: "10px" }}>
                  <img
                    src={img}
                    alt="preview"
                    style={{
                      width: "100%",
                      borderRadius: "8px",
                      marginBottom: "5px"
                    }}
                  />
                  <div style={{ display: "flex", gap: "10px", fontSize: "12px" }}>
                    <a href={img} target="_blank">🔍 Preview</a>
                    <a href={img} download>⬇ Download</a>
                  </div>
                </div>
              ))}

              {/* PDFs */}
              {m.pdfs && m.pdfs.map((pdf, idx) => (
                <div key={idx} style={{ marginTop: "6px" }}>
                  <a href={pdf} target="_blank">📄 View PDF</a>
                </div>
              ))}

            </div>
          </div>
        ))}

        {loading && <div style={{ fontSize: "12px" }}>Typing...</div>}

        <div ref={chatEndRef}></div>
      </div>

      {/* INPUT */}
      <div style={{
        display: "flex",
        padding: "10px",
        borderTop: "1px solid #eee"
      }}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type message..."
          style={{
            flex: 1,
            padding: "8px",
            borderRadius: "8px",
            border: "1px solid #ccc"
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") sendQuery();
          }}
        />

        <button
          onClick={() => sendQuery()}
          style={{
            marginLeft: "5px",
            background: "#d32f2f",
            color: "#fff",
            border: "none",
            borderRadius: "8px",
            padding: "8px 12px",
            cursor: "pointer"
          }}
        >
          ➤
        </button>
      </div>

      {/* LANGUAGE */}
      <div style={{ padding: "6px 10px", fontSize: "13px" }}>
        🌐
        <select
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          style={{ marginLeft: "5px" }}
        >
          <option value="auto">Auto</option>
          <option value="en">English</option>
          <option value="hi">Hindi</option>
          <option value="mr">Marathi</option>
        </select>
      </div>

    </div>
  );
}