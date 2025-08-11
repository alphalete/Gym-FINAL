import * as React from "react";
import { getSetting } from "./settingsStore";
export function useSetting(key, fallback = null) {
  const [val, setVal] = React.useState(fallback);
  React.useEffect(() => { (async () => setVal(await getSetting(key)))(); }, [key]);
  return val;
}