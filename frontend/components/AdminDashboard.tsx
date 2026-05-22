



"use client"

import { useState, useEffect } from "react"

const API = "http://localhost:8000"
const ADMIN_PASSWORD = "Mayur@admin00"

export default function AdminDashboard() {
  const [authed, setAuthed]     = useState(false)
  const [pw, setPw]             = useState("")
  const [companies, setCompanies] = useState<any[]>([])
  const [users, setUsers]       = useState<any[]>([])
  const [tab, setTab]           = useState<"companies"|"users">("companies")
  const [loading, setLoading]   = useState(false)
  const [msg, setMsg]           = useState("")

  // Hooks must all be declared before any conditional return
  useEffect(() => {
    if (authed) load()
  }, [authed])

  const load = async () => {
    setLoading(true)
    const [c, u] = await Promise.all([
      fetch(`${API}/api/v1/auth/admin/companies`).then(r => r.json()),
      fetch(`${API}/api/v1/auth/admin/users`).then(r => r.json()),
    ])
    setCompanies(c)
    setUsers(u)
    setLoading(false)
  }

  const activate = async (company_id: string, plan: string, days: number) => {
    const res = await fetch(`${API}/api/v1/auth/admin/activate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_id, plan, days }),
    })
    const data = await res.json()
    setMsg(data.message)
    load()
  }

  const block = async (company_id: string) => {
    if (!confirm("Block this company? They will lose access immediately.")) return
    const res = await fetch(`${API}/api/v1/auth/admin/block`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_id, reason: "non-payment" }),
    })
    const data = await res.json()
    setMsg(data.message)
    load()
  }

  const unblock = async (company_id: string) => {
    const res = await fetch(`${API}/api/v1/auth/admin/unblock`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_id, reason: "reinstated" }),
    })
    const data = await res.json()
    setMsg(data.message)
    load()
  }

  const statusColor = (status: string) => ({
    "active-trial":    "#f59e0b",
    "active-paid":     "#10b981",
    "trial-expired":   "#ef4444",
    "payment-overdue": "#ef4444",
    "blocked":         "#991b1b",
  }[status] || "#6b7280")

  const planBg = (plan: string) => ({
    trial:   "#fffbeb",
    starter: "#eff6ff",
    growth:  "#f5f3ff",
    scale:   "#ecfdf5",
  }[plan] || "#f9fafb")

  const s = {
    fontSize: 12, padding: "4px 10px", borderRadius: 6,
    border: "none", cursor: "pointer", fontWeight: 600
  }

  // ── Auth gate — after all hooks ──────────────────────────────────────────
  if (!authed) {
    return (
      <div style={{ minHeight:"100vh", display:"flex", alignItems:"center", justifyContent:"center", background:"#f8f9fc", fontFamily:"system-ui" }}>
        <div style={{ background:"#fff", border:"1px solid #e5e7eb", borderRadius:12, padding:32, width:320 }}>
          <div style={{ fontWeight:800, fontSize:18, color:"#111827", marginBottom:4 }}>Admin Access</div>
          <div style={{ fontSize:12, color:"#9ca3af", marginBottom:20 }}>HireAgent internal dashboard</div>
          <input
            type="password"
            placeholder="Enter admin password"
            value={pw}
            onChange={e => setPw(e.target.value)}
            onKeyDown={e => { if (e.key === "Enter") { if (pw === ADMIN_PASSWORD) setAuthed(true); else alert("Wrong password") }}}
            style={{ width:"100%", padding:"10px 12px", border:"1px solid #e5e7eb", borderRadius:8, fontSize:14, marginBottom:12, boxSizing:"border-box" as const }}
          />
          <button
            onClick={() => { if (pw === ADMIN_PASSWORD) setAuthed(true); else alert("Wrong password") }}
            style={{ width:"100%", padding:10, background:"#6366f1", color:"#fff", border:"none", borderRadius:8, fontWeight:700, fontSize:14, cursor:"pointer" }}
          >
            Enter
          </button>
        </div>
      </div>
    )
  }

  // ── Main dashboard ────────────────────────────────────────────────────────
  if (loading) return (
    <div style={{ minHeight:"100vh", display:"flex", alignItems:"center", justifyContent:"center", fontFamily:"system-ui" }}>
      <div style={{ fontSize:14, color:"#6b7280" }}>Loading...</div>
    </div>
  )

  return (
    <div style={{ minHeight:"100vh", background:"#f8f9fc", fontFamily:"system-ui, sans-serif" }}>

      {/* Header */}
      <div style={{ background:"#fff", borderBottom:"1px solid #e5e7eb", padding:"0 24px" }}>
        <div style={{ maxWidth:1100, margin:"0 auto", display:"flex", alignItems:"center", justifyContent:"space-between", height:56 }}>
          <div style={{ display:"flex", alignItems:"center", gap:10 }}>
            <div style={{ width:32, height:32, background:"#ef4444", borderRadius:8, display:"flex", alignItems:"center", justifyContent:"center", color:"#fff", fontWeight:800 }}>A</div>
            <span style={{ fontWeight:800, fontSize:16, color:"#111827" }}>HireAgent Admin</span>
          </div>
          <div style={{ display:"flex", gap:8 }}>
            <span style={{ fontSize:12, background:"#ecfdf5", color:"#065f46", padding:"3px 10px", borderRadius:20, fontWeight:600 }}>{companies.filter(c=>c.is_active).length} active</span>
            <span style={{ fontSize:12, background:"#fef2f2", color:"#991b1b", padding:"3px 10px", borderRadius:20, fontWeight:600 }}>{companies.filter(c=>!c.is_active).length} blocked</span>
            <span style={{ fontSize:12, background:"#eff6ff", color:"#1d4ed8", padding:"3px 10px", borderRadius:20, fontWeight:600 }}>{users.length} users</span>
          </div>
        </div>
      </div>

      {/* Message */}
      {msg && (
        <div style={{ background:"#ecfdf5", border:"1px solid #a7f3d0", padding:"10px 24px", fontSize:13, color:"#065f46", display:"flex", justifyContent:"space-between" }}>
          {msg}
          <button onClick={()=>setMsg("")} style={{ background:"none", border:"none", cursor:"pointer", color:"#065f46", fontWeight:700 }}>x</button>
        </div>
      )}

      {/* Tabs */}
      <div style={{ background:"#fff", borderBottom:"1px solid #e5e7eb", padding:"0 24px" }}>
        <div style={{ maxWidth:1100, margin:"0 auto", display:"flex" }}>
          {(["companies","users"] as const).map(t=>(
            <button key={t} onClick={()=>setTab(t)}
              style={{ padding:"12px 20px", border:"none", background:"transparent", fontSize:13, fontWeight:tab===t?700:500, color:tab===t?"#6366f1":"#6b7280", borderBottom:tab===t?"2px solid #6366f1":"2px solid transparent", cursor:"pointer", textTransform:"capitalize" }}>
              {t} ({t==="companies"?companies.length:users.length})
            </button>
          ))}
          <button onClick={load} style={{ marginLeft:"auto", fontSize:12, color:"#6b7280", background:"#f9fafb", border:"1px solid #e5e7eb", borderRadius:6, padding:"4px 12px", cursor:"pointer", alignSelf:"center" }}>
            Refresh
          </button>
        </div>
      </div>

      <div style={{ maxWidth:1100, margin:"24px auto", padding:"0 24px" }}>

        {/* Companies */}
        {tab==="companies" && companies.map(c=>(
          <div key={c.id} style={{ background:"#fff", border:"1px solid #e5e7eb", borderRadius:12, padding:"16px 20px", marginBottom:12, opacity:c.is_active?1:0.7 }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
              <div>
                <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:4 }}>
                  <span style={{ fontWeight:700, fontSize:15, color:"#111827" }}>{c.name}</span>
                  <span style={{ fontSize:11, background:planBg(c.plan), color:"#374151", padding:"2px 8px", borderRadius:10, fontWeight:600 }}>{c.plan}</span>
                  <span style={{ fontSize:11, color:statusColor(c.status), fontWeight:600 }}>{c.status}</span>
                  {!c.is_active && <span style={{ fontSize:11, background:"#fef2f2", color:"#991b1b", padding:"2px 8px", borderRadius:10, fontWeight:700 }}>BLOCKED</span>}
                </div>
                <div style={{ fontSize:11, color:"#9ca3af", marginBottom:2 }}>ID: {c.id}</div>
                <div style={{ fontSize:11, color:"#9ca3af" }}>
                  {c.plan==="trial"
                    ? `Trial ends: ${c.trial_ends_at ? new Date(c.trial_ends_at).toLocaleDateString() : "not set"}`
                    : `Paid until: ${c.paid_until ? new Date(c.paid_until).toLocaleDateString() : "not set"}`
                  }
                  {" · "}{c.days_left} days left · Registered: {c.created_at ? new Date(c.created_at).toLocaleDateString() : "unknown"}
                </div>
              </div>
              <div style={{ display:"flex", gap:6, flexWrap:"wrap", justifyContent:"flex-end", maxWidth:320 }}>
                {c.is_active ? (
                  <>
                    <button onClick={()=>activate(c.id,"starter",30)} style={{...s, background:"#eff6ff", color:"#1d4ed8"}}>+30d Starter</button>
                    <button onClick={()=>activate(c.id,"growth",30)}  style={{...s, background:"#f5f3ff", color:"#6d28d9"}}>+30d Growth</button>
                    <button onClick={()=>activate(c.id,"trial",14)}   style={{...s, background:"#fffbeb", color:"#92400e"}}>+14d Trial</button>
                    <button onClick={()=>block(c.id)}                 style={{...s, background:"#fef2f2", color:"#991b1b"}}>Block</button>
                  </>
                ) : (
                  <button onClick={()=>unblock(c.id)} style={{...s, background:"#ecfdf5", color:"#065f46"}}>Unblock + Reset Trial</button>
                )}
              </div>
            </div>
          </div>
        ))}

        {/* Users */}
        {tab==="users" && (
          <div style={{ background:"#fff", border:"1px solid #e5e7eb", borderRadius:12, overflow:"hidden" }}>
            <table style={{ width:"100%", borderCollapse:"collapse" }}>
              <thead>
                <tr style={{ background:"#f9fafb", borderBottom:"1px solid #e5e7eb" }}>
                  {["Name","Email","Company","Plan","Role","Last Login","Joined"].map(h=>(
                    <th key={h} style={{ padding:"10px 16px", fontSize:11, fontWeight:700, color:"#6b7280", textAlign:"left", textTransform:"uppercase", letterSpacing:"0.05em" }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {users.map((u,i)=>(
                  <tr key={u.user_id} style={{ borderBottom:"1px solid #f3f4f6", background:i%2===0?"#fff":"#fafafa" }}>
                    <td style={{ padding:"10px 16px", fontSize:13, fontWeight:600, color:"#111827" }}>{u.full_name}</td>
                    <td style={{ padding:"10px 16px", fontSize:12, color:"#6b7280" }}>{u.email}</td>
                    <td style={{ padding:"10px 16px", fontSize:12, color:"#374151" }}>{u.company_name}</td>
                    <td style={{ padding:"10px 16px" }}>
                      <span style={{ fontSize:11, background:planBg(u.company_plan), color:"#374151", padding:"2px 7px", borderRadius:8, fontWeight:600 }}>{u.company_plan}</span>
                    </td>
                    <td style={{ padding:"10px 16px", fontSize:12, color:"#6b7280" }}>{u.role}</td>
                    <td style={{ padding:"10px 16px", fontSize:11, color:"#9ca3af" }}>{u.last_login==="never"?"never":new Date(u.last_login).toLocaleDateString()}</td>
                    <td style={{ padding:"10px 16px", fontSize:11, color:"#9ca3af" }}>{u.created_at?new Date(u.created_at).toLocaleDateString():""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}









