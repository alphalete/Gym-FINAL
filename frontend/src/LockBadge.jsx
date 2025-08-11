import * as React from "react";
import { useSetting } from "./useSetting";
export default function LockBadge({ className = "ml-1" }) {
  const enabled = useSetting("paymentsPinEnabled", false);
  if (!enabled) return null;
  return <span className={className} aria-hidden>🔒</span>;
}