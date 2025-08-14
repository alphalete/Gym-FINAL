import { useEffect, useState } from "react";
import repo from "../data/members.repo";

export default function useMembersRepo(){
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = async () => {
    try { setMembers(await repo.listMembers()); }
    catch(e){ setError(e); }
    finally { setLoading(false); }
  };

  useEffect(() => { let live = true; (async()=>{
    try { const arr = await repo.listMembers(); if(live) setMembers(arr); }
    catch(e){ if(live) setError(e); }
    finally { if(live) setLoading(false); }
  })(); return () => { live = false; }; }, []);

  return { members, setMembers, loading, error, refresh, repo };
}