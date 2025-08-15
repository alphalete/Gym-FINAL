import { useEffect, useState } from "react";
import repo from "../data/members.repo";

export default function useMembersRepo(){
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = async () => {
    console.log('🔄 useMembersRepo: Refreshing members data...');
    try { 
      const newMembers = await repo.listMembers(); 
      setMembers(newMembers);
      console.log('✅ useMembersRepo: Refreshed with', newMembers.length, 'members');
    }
    catch(e){ 
      console.error('❌ useMembersRepo: Refresh error:', e);
      setError(e); 
    }
    finally { setLoading(false); }
  };

  useEffect(() => { 
    let live = true; 
    
    (async()=>{
      try { 
        const arr = await repo.listMembers(); 
        if(live) {
          setMembers(arr);
          console.log('📊 useMembersRepo: Initial load with', arr.length, 'members');
        }
      }
      catch(e){ 
        if(live) {
          setError(e);
          console.error('❌ useMembersRepo: Initial load error:', e);
        }
      }
      finally { if(live) setLoading(false); }
    })(); 
    
    // CRITICAL: Listen for DATA_CHANGED events to refresh UI
    const handleDataChanged = (event) => {
      console.log('🔔 useMembersRepo: DATA_CHANGED event received:', event.detail);
      if (event.detail === 'member_deleted' || event.detail === 'member_updated' || event.detail === 'member_added') {
        refresh();
      }
    };

    window.addEventListener('DATA_CHANGED', handleDataChanged);
    
    return () => { 
      live = false; 
      window.removeEventListener('DATA_CHANGED', handleDataChanged);
    }; 
  }, []);

  return { members, setMembers, loading, error, refresh, repo };
}