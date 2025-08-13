import * as store from "../storage";
import { useEffect, useState } from "react";

export default function useMembersFromStorage(){
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => { 
    let live = true;
    (async () => {
      try {
        await (store.init?.());
        const data = await (store.getAllMembers?.());
        if (live) setMembers(Array.isArray(data) ? data : []);
      } catch (e) { 
        if (live) setError(e); 
      } finally { 
        if (live) setLoading(false); 
      }
    })(); 
    return () => { live = false; }; 
  }, []);
  
  return { members, setMembers, loading, error };
}