import React, { useState } from "react";
import ChatWidget from "./components/ChatWidget";

export default function App() {

  const [open, setOpen] = useState(false);

  return (
    <>
      {/* FLOATING BUTTON */}
      <div
        onClick={() => setOpen(!open)}
        style={{
          position: "fixed",
          bottom: "20px",
          right: "20px",
          width: "60px",
          height: "60px",
          borderRadius: "50%",
          background: "#d32f2f",
          color: "#fff",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "24px",
          cursor: "pointer",
          zIndex: 9999,
          boxShadow: "0 4px 10px rgba(0,0,0,0.3)"
        }}
      >
        💬
      </div>

      {/* CHAT WINDOW */}
      {open && <ChatWidget close={() => setOpen(false)} />}
    </>
  );
}