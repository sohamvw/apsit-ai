import React, { useState } from "react";

const BACKEND_URL = "https://apsit-ai.onrender.com";

export default function ChatWidget() {

  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);

  const session_id = "demo-session";

  const sendQuery = async () => {

    const res = await fetch(`${BACKEND_URL}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        session_id
      })
    });

    const data = await res.json();

    setResponse(data);
  };

  return (

    <div style={{
      position:"fixed",
      bottom:"20px",
      right:"20px",
      background:"#fff",
      padding:"15px",
      borderRadius:"10px",
      boxShadow:"0 0 10px #ccc",
      width:"320px"
    }}>

      <h4>APSIT AI Assistant</h4>

      <input
        value={query}
        onChange={(e)=>setQuery(e.target.value)}
        placeholder="Ask about APSIT..."
        style={{width:"100%"}}
      />

      <button
        onClick={sendQuery}
        style={{marginTop:"10px"}}
      >
        Send
      </button>

      {response && (

        <div style={{marginTop:"15px"}}>

          <p>{response.answer}</p>

          {response.pdfs.length > 0 && (
            <>
              <h5>Documents</h5>

              {response.pdfs.map((pdf, i) => (
                <div key={i}>
                  <a href={pdf} target="_blank" rel="noreferrer">
                    View PDF
                  </a>
                </div>
              ))}

            </>
          )}

        </div>

      )}

    </div>
  );
}