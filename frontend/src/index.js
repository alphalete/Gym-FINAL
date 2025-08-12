import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

// Temporarily unregister SW to break cache on phone (remove later)
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(regs => regs.forEach(r => r.unregister()));
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
