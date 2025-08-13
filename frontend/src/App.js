import React, { useEffect, useMemo, useState } from "react";
import "./App.css";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import Components from "./Components";
import gymStorage from "./storage";
import ErrorBoundary from "./ErrorBoundary";
import BottomNav from "./components/BottomNav";

const Fallback = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="animate-pulse text-gray-600">Loading…</div>
  </div>
);

// Be defensive: Components default-exports an object of subcomponents
const safe = (C, name) => (C && C[name]) || (() => <div className="p-4">Missing component: {name}</div>);

export default function App(){
  const [ready, setReady] = useState(false);
  const [authed, setAuthed] = useState(true); // if you gate by login, wire true/false accordingly
  
  const C = useMemo(() => ({
    Sidebar: safe(Components, "Sidebar"),
    Dashboard: safe(Components, "Dashboard"),
    ClientManagement: safe(Components, "ClientManagement"),
    PaymentTracking: safe(Components, "PaymentTracking"),
    MembershipManagement: safe(Components, "MembershipManagement"),
    Reports: safe(Components, "Reports"),
    Settings: safe(Components, "Settings"),
    LoginForm: safe(Components, "LoginForm"),
    InstallPrompt: safe(Components, "InstallPrompt"),
  }), [Components]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        console.log("[App] Initializing storage...");
        // Init IndexedDB (with fallback in storage.js)
        await gymStorage.init?.();
        await gymStorage.persistHint?.();
        console.log("[App] Storage initialized successfully");
      } catch (e) {
        console.warn("[App] storage init failed (continuing):", e);
      } finally {
        if (!cancelled) {
          setReady(true);
          // Dismiss HTML loading screen now that React is ready
          setTimeout(() => {
            const loadingScreen = document.getElementById('loading-screen');
            if (loadingScreen) {
              loadingScreen.style.display = 'none';
              console.log("[App] HTML loading screen dismissed");
            }
          }, 100);
        }
      }
    })();
    
    // (Optional) During dev, avoid stale SW keeping old broken bundles
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.getRegistrations?.().then(rs => {
        rs.forEach(r => {
          if (process.env.NODE_ENV !== "production") r.unregister();
        });
      }).catch(()=>{});
    }
    return () => { cancelled = true; };
  }, []);

  if (!ready) return <Fallback />;

  return (
    <ErrorBoundary>
      <HashRouter>
        {!authed ? (
          <C.LoginForm onLogin={() => setAuthed(true)} />
        ) : (
          <div className="min-h-screen bg-soft flex">
            <C.Sidebar />
            <main className="flex-1 min-w-0 pb-20 md:pb-4 md:ml-16">
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<C.Dashboard />} />
                <Route path="/members" element={<C.ClientManagement />} />
                <Route path="/payments" element={<C.PaymentTracking />} />
                <Route path="/plans" element={<C.MembershipManagement />} />
                <Route path="/reports" element={<C.Reports />} />
                <Route path="/settings" element={<C.Settings />} />
                <Route path="*" element={<div className="p-4">Not found</div>} />
              </Routes>
            </main>
            <BottomNav />
          </div>
        )}
      </HashRouter>
    </ErrorBoundary>
  );
}