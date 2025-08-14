import { useEffect, useState } from "react";
import facade from "../storage.facade";

export default function useMembersFromStorage(){
  const [members,setMembers]=useState([]); 
  const [loading,setLoading]=useState(true); 
  const [error,setError]=useState(null);
  
  useEffect(()=>{ 
    let live=true;
    (async()=>{
      try{ 
        await facade.init(); 
        const m = await facade.getAllMembers(); 
        if(live) setMembers(Array.isArray(m)?m:[]); 
      } catch(e){ 
        if(live) setError(e); 
      } finally{ 
        if(live) setLoading(false); 
      }
    })(); 
    return ()=>{ live=false; }; 
  },[]);
  
  return { members, setMembers, loading, error };
}