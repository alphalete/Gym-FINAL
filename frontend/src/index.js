import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import "./styles/tokens.css";   // make sure this import exists
import App from "./App";

// Unregister any existing service workers to avoid stale cache
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(rs => rs.forEach(r => r.unregister()));
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
