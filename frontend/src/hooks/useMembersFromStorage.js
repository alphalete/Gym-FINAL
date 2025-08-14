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
        
        // Get members using direct storage access
        let m = [];
        if (storage.getAllMembers) {
          m = await storage.getAllMembers();
        } else if (storageNamed.getAllMembers) {
          m = await storageNamed.getAllMembers();
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