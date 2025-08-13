import React from "react";

export default function DebugOverlay({ error, info }) {
  if (!error) return null;
  return (
    <div style={{
      position:"fixed", inset:0, background:"rgba(255,255,255,0.96)",
      zIndex: 9999, padding:"16px", fontFamily:"system-ui,Segoe UI,Roboto"
    }}>
      <h2 style={{margin:"0 0 8px"}}>Runtime error</h2>
      <pre style={{whiteSpace:"pre-wrap", background:"#f3f4f6", padding:12, borderRadius:8, border:"1px solid #e5e7eb"}}>
{String(error?.message || error)}
      </pre>
      {info?.componentStack && (
        <details style={{marginTop:8}}>
          <summary>Component stack</summary>
          <pre style={{whiteSpace:"pre-wrap"}}>{info.componentStack}</pre>
        </details>
      )}
    </div>
  );
}