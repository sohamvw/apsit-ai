import React, { useState, useEffect } from "react";

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL;

const QUICK_DEFAULT = [
  "Admissions",
  "Placements",
  "Courses Offered",
  "Facilities"
];

export default function ChatWidget() {

  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [topQueries, setTopQueries] = useState(QUICK_DEFAULT);
  const [language, setLanguage] = useState("auto");

  const session_id = "apsit-session";

  // 🔥 Track popular queries (local frequency)
  const updateTopQueries = (q) => {
    let stored = JSON.parse(localStorage.getItem("topQueries")) || {};

    stored[q] = (stored[q] || 0) + 1;

    localStorage.setItem("topQueries", JSON.stringify(stored));

    const sorted = Object.entries(stored)
      .sort((a, b) => b[1] - a[1])
      .map(x => x[0])
      .slice(0, 4);

    setTopQueries(sorted.length ? sorted : QUICK_DEFAULT);
  };

  useEffect(() => {
    updateTopQueries("");
  }, []);

  const sendQuery = async (customQuery) => {

    const finalQuery = customQuery || query;
    if (!finalQuery) return;

    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          query: finalQuery,
          session_id,
          language
        })
      });

      const data = await res.json();

      setResponse(data);
      updateTopQueries(finalQuery);
      setQuery("");

    } catch (e) {
      console.error(e);
    }

    setLoading(false);
  };

  return (

    <div style={{
      position: "fixed",
      bottom: "20px",
      right: "20px",
      width: "340px",
      fontFamily: "Arial",
      zIndex: 9999
    }}>

      {/* HEADER */}
      <div style={{
        background: "#8B4513",  // APSIT brown
        color: "#fff",
        padding: "10px",
        borderTopLeftRadius: "12px",
        borderTopRightRadius: "12px"
      }}>
        <b>APSIT Virtual Assistant</b>

        <div style={{ fontSize: "12px" }}>
          Online | Instant replies
        </div>
      </div>

      {/* BODY */}
      <div style={{
        background: "#f9f6f2",
        padding: "10px",
        border: "1px solid #ddd"
      }}>

        <div style={{
          background: "#fff",
          padding: "8px",
          borderRadius: "8px",
          marginBottom: "10px"
        }}>
          👋 Hello! Ask me anything about APSIT.
        </div>

        {/* QUICK ACTIONS */}
        <div style={{ marginBottom: "10px" }}>
          {topQueries.map((q, i) => (
            <button
              key={i}
              onClick={() => sendQuery(q)}
              style={{
                margin: "4px",
                padding: "6px 10px",
                borderRadius: "20px",
                border: "1px solid #8B4513",
                background: "#fff",
                cursor: "pointer"
              }}
            >
              {q}
            </button>
          ))}
        </div>

        {/* RESPONSE */}
        {response && (
          <div style={{
            background: "#fff",
            padding: "8px",
            borderRadius: "8px",
            marginBottom: "10px"
          }}>
            {response.answer}

            {response.pdfs?.length > 0 && (
              <>
                <div style={{ marginTop: "10px", fontWeight: "bold" }}>
                  Documents:
                </div>

                {response.pdfs.map((pdf, i) => (
                  <div key={i}>
                    <a href={pdf} target="_blank">📄 View PDF</a>
                  </div>
                ))}
              </>
            )}
          </div>
        )}

        {/* LANGUAGE SELECTOR */}
        <div style={{ marginBottom: "8px" }}>
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

        {/* INPUT */}
        <div style={{ display: "flex" }}>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type your message..."
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
              background: "#8B4513",
              color: "#fff",
              border: "none",
              borderRadius: "8px",
              padding: "8px 10px",
              cursor: "pointer"
            }}
          >
            ➤
          </button>
        </div>

        {loading && <div style={{ fontSize: "12px" }}>Thinking...</div>}

      </div>

    </div>
  );
}