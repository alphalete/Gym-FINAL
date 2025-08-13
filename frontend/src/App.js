import React, { useEffect, useMemo, useState } from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";
import ErrorBoundary from "./ErrorBoundary";
import gymStorage, * as storageNamed from "./storage";
import Components from "./Components";
import BottomNav from "./components/BottomNav";

const Fallback = () => (
  <div className="min-h-screen flex items-center justify-center text-gray-600">Loading…</div>
);

const safePick = (bag, key) => (bag && bag[key]) ? bag[key] : (() => <div className="p-4">Missing component: {key}</div>);

export default function App(){
  const [ready, setReady] = useState(false);

  const C = useMemo(() => ({
    Sidebar:              safePick(Components, "Sidebar"),
    Dashboard:            safePick(Components, "Dashboard"),
    ClientManagement:     safePick(Components, "ClientManagement"),
    PaymentTracking:      safePick(Components, "PaymentTracking"),
    MembershipManagement: safePick(Components, "MembershipManagement"),
    Reports:              safePick(Components, "Reports"),
    Settings:             safePick(Components, "Settings"),
    LoginForm:            safePick(Components, "LoginForm"),
    InstallPrompt:        safePick(Components, "InstallPrompt"),
  }), []);

  useEffect(() => {
    let cancelled = false;
    
    // 1) Kill dev SW caches so we don't serve stale JS
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.getRegistrations?.().then(rs => rs.forEach(r => r.unregister())).catch(()=>{});
      caches?.keys?.().then(keys => keys.forEach(k => caches.delete(k))).catch(()=>{});
    }
    
    // 2) Safe init with a hard timeout so UI always mounts
    const hardTimeout = setTimeout(() => {
      if (!cancelled) {
        console.warn("[App] storage init timeout; continuing with UI");
        setReady(true);
        // Force dismiss loading screen on timeout
        setTimeout(() => {
          const loadingScreen = document.getElementById('loading-screen');
          if (loadingScreen) {
            loadingScreen.style.display = 'none';
            console.log("[App] Loading screen force dismissed on timeout");
          }
        }, 100);
      }
    }, 4000);

    (async () => {
      try {
        console.log("[App] Starting safe initialization...");
        // Try both default and named to cover different storage shapes
        await (gymStorage?.init?.() ?? storageNamed?.init?.?.() ?? Promise.resolve());
        await (gymStorage?.persistHint?.() ?? storageNamed?.persistHint?.?.() ?? Promise.resolve());
        window.__BOOT_OK__ = true;
        console.log("[App] Safe initialization completed");
      } catch (e) {
        console.error("[App] init error (continuing):", e);
      } finally {
        clearTimeout(hardTimeout);
        if (!cancelled) {
          setReady(true);
          // Dismiss loading screen when ready
          setTimeout(() => {
            const loadingScreen = document.getElementById('loading-screen');
            if (loadingScreen) {
              loadingScreen.style.display = 'none';
              console.log("[App] Loading screen dismissed after safe init");
            }
          }, 100);
        }
      }
    })();

    return () => { cancelled = true; clearTimeout(hardTimeout); };
  }, []);

  if (!ready) return <Fallback />;

  return (
    <ErrorBoundary>
      <HashRouter>
        <div className="min-h-screen bg-soft flex">
          <C.Sidebar />
          <main className="flex-1 min-w-0 pb-20 md:pb-4 md:ml-16">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<C.Dashboard />} />
              <Route path="/members" element={<C.ClientManagement />} />
              <Route path="/plans" element={<C.MembershipManagement />} />
              <Route path="/payments" element={<C.PaymentTracking />} />
              <Route path="/reports" element={<C.Reports />} />
              <Route path="/settings" element={<C.Settings />} />
              <Route path="*" element={<div className="p-4">Not found</div>} />
            </Routes>
          </main>
          <BottomNav />
        </div>
      </HashRouter>
    </ErrorBoundary>
  );
}