import { useEffect, useState } from "react";
import storageDefault, * as storageNamed from "../storage";

export default function useMembersFromStorage(){
  const [members,setMembers]=useState([]); 
  const [loading,setLoading]=useState(true); 
  const [error,setError]=useState(null);
  
  useEffect(()=>{ 
    let live=true;
    (async()=>{
      try{ 
        // Initialize storage
        const storage = storageDefault || storageNamed;
        if (storage.init) {
          await storage.init();
        }
        
        // First try to get members from backend (primary source)
        let m = [];
        try {
          const backendUrl = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
          if (backendUrl) {
            const response = await fetch(`${backendUrl}/api/clients`);
            if (response.ok) {
              const backendMembers = await response.json();
              if (Array.isArray(backendMembers) && backendMembers.length > 0) {
                m = backendMembers;
                console.log(`✅ Loaded ${m.length} members from backend`);
              }
            }
          }
        } catch (backendError) {
          console.warn('⚠️ Backend connection failed, falling back to local storage:', backendError.message);
        }
        
        // If no backend data, try local storage
        if (m.length === 0) {
          if (storage.getAllMembers) {
            m = await storage.getAllMembers();
          } else if (storageNamed.getAllMembers) {
            m = await storageNamed.getAllMembers();
          }
          console.log(`📱 Loaded ${m.length} members from local storage`);
        }
        
        if(live) setMembers(Array.isArray(m)?m:[]); 
      } catch(e){ 
        console.error('[useMembersFromStorage] Error:', e);
        if(live) setError(e); 
      } finally{ 
        if(live) setLoading(false); 
      }
    })(); 
    return ()=>{ live=false; }; 
  },[]);
  
  return { members, setMembers, loading, error };
}