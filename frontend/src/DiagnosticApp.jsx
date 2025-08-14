import React from "react";
import Components from "./Components";
import storageDefault, * as storageNamed from "./storage";
import storageFacade from "./storage.facade";
import membersRepo from "./data/members.repo";

const Row = ({k,v}) => (
  <div style={{
    display: "flex",
    justifyContent: "space-between",
    padding: "6px 0",
    borderBottom: "1px solid #eee"
  }}>
    <strong>{k}</strong>
    <span style={{
      color: v === true ? "#16a34a" : (v instanceof Error ? "#dc2626" : "#6b7280")
    }}>
      {v instanceof Error ? v.message : String(v)}
    </span>
  </div>
);

export default function DiagnosticApp(){
  const [o, setO] = React.useState({});
  
  React.useEffect(() => {
    (async () => {
      const out = {};
      
      try { 
        out.ComponentsObject = !!Components; 
      } catch(e) { 
        out.ComponentsObject = e; 
      }
      
      out.ComponentKeys = Components ? Object.keys(Components).join(", ") : "none";
      
      const need = ["Sidebar","Dashboard","ClientManagement","PaymentTracking","MembershipManagement","Reports","Settings","LoginForm","InstallPrompt"];
      out.Missing = need.filter(k => !Components || !Components[k]).join(", ") || true;
      
      out.storageDefault = !!storageDefault;
      
      try { 
        const m = await storageFacade.getAllMembers();
        out.getAllMembersOK = Array.isArray(m);
      } catch(e) { 
        out.getAllMembersOK = e; 
      }
      
      // Members repository diagnostics
      try {
        const before = await membersRepo.listMembers();
        out.MembersRepoListOK = Array.isArray(before);
        const tmp = { name:"_diag_", email:"_", phone:"_" };
        const afterUpsert = await membersRepo.upsertMember(tmp);
        out.MembersRepoUpsertOK = Array.isArray(afterUpsert) && afterUpsert.some(x => x.name==="_diag_");
        const diagId = afterUpsert.find(x => x.name==="_diag_")?.id ?? afterUpsert.find(x => x.name==="_diag_")?._id;
        const afterDelete = await membersRepo.removeMember(diagId);
        out.MembersRepoDeleteOK = Array.isArray(afterDelete) && !afterDelete.some(x => x.name==="_diag_");
      } catch(e){ out.MembersRepoError = e?.message || String(e); }
      
      setO(out);
    })();
  }, []);
  
  return (
    <div style={{
      padding: 16,
      fontFamily: "system-ui, -apple-system, Segoe UI, Roboto"
    }}>
      <h1 style={{ margin: "0 0 12px" }}>Diagnostics</h1>
      {Object.entries(o).map(([k,v]) => <Row key={k} k={k} v={v}/>)}
      <div style={{ marginTop: 12 }}>
        <a href="#/dashboard" style={{ marginRight: 12 }}>Go to dashboard</a>
        <button onClick={() => location.reload()} style={{ padding: "6px 10px" }}>
          Reload
        </button>
      </div>
    </div>
  );
}