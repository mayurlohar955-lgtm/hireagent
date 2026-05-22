"use client"

import { useState } from "react"

// ─── Types ────────────────────────────────────────────────────────────────────

type AuthMode = "login" | "register"

interface AuthResponse {
  token:   string
  user:    { id: string; email: string; full_name: string; role: string }
  company: { id: string; name: string; slug: string; plan: string }
  message?: string
}

// ─── Token helpers (localStorage) ────────────────────────────────────────────

export const saveAuth = (data: AuthResponse) => {
  localStorage.setItem("hr_token",   data.token)
  localStorage.setItem("hr_user",    JSON.stringify(data.user))
  localStorage.setItem("hr_company", JSON.stringify(data.company))
  document.cookie = `hr_token=${data.token}; path=/; max-age=${7 * 24 * 60 * 60}`
}

export const getToken    = () => localStorage.getItem("hr_token")
export const getUser     = () => { const u = localStorage.getItem("hr_user");    return u ? JSON.parse(u) : null }
export const getCompany  = () => { const c = localStorage.getItem("hr_company"); return c ? JSON.parse(c) : null }
export const isLoggedIn  = () => !!getToken()
export const logout = () => {
  localStorage.removeItem("hr_token")
  localStorage.removeItem("hr_user")
  localStorage.removeItem("hr_company")
  document.cookie = "hr_token=; path=/; max-age=0"
  window.location.href = "/auth"
}
// ─── Authed fetch wrapper ─────────────────────────────────────────────────────

export const authFetch = async (url: string, options: RequestInit = {}) => {
  const token = getToken()
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  })
  if (res.status === 401) { logout(); return res }
  return res
}

// ─── Auth Page Component ──────────────────────────────────────────────────────

export default function AuthPage() {
  const [mode, setMode]       = useState<AuthMode>("login")
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState("")
  const [form, setForm]       = useState({
    email: "", password: "", full_name: "", company_name: ""
  })

  const inp = {
    width: "100%", padding: "10px 12px", border: "1px solid #e5e7eb",
    borderRadius: 8, fontSize: 14, color: "#111827", outline: "none",
    boxSizing: "border-box" as const, marginBottom: 12,
  }
  const lbl = { fontSize: 12, fontWeight: 600, color: "#374151", display: "block", marginBottom: 4 } as const

  const handleSubmit = async () => {
    setError(""); setLoading(true)
    try {
      const endpoint = mode === "login" ? "/api/v1/auth/login" : "/api/v1/auth/register"
      const body     = mode === "login"
        ? { email: form.email, password: form.password }
        : { email: form.email, password: form.password, full_name: form.full_name, company_name: form.company_name }

      const res  = await fetch(endpoint, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(body),
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || "Something went wrong")
      } else {
        saveAuth(data)
        window.location.href = "/"   // redirect to main app
      }
    } catch (e) {
      setError("Network error — is the backend running?")
    }
    setLoading(false)
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f8f9fc", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "system-ui, sans-serif" }}>
      <div style={{ width: 420, background: "#fff", borderRadius: 16, border: "1px solid #e5e7eb", padding: 32, boxShadow: "0 4px 24px rgba(0,0,0,0.06)" }}>

        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 28 }}>
          <div style={{ width: 36, height: 36, background: "#6366f1", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 800, fontSize: 18 }}>H</div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 18, color: "#111827" }}>HireAgent</div>
            <div style={{ fontSize: 11, color: "#9ca3af" }}>AI-powered recruitment</div>
          </div>
        </div>

        {/* Mode toggle */}
        <div style={{ display: "flex", background: "#f3f4f6", borderRadius: 8, padding: 4, marginBottom: 24 }}>
          {(["login", "register"] as AuthMode[]).map(m => (
            <button key={m} onClick={() => { setMode(m); setError("") }}
              style={{ flex: 1, padding: "7px 0", border: "none", borderRadius: 6, fontSize: 13, fontWeight: 600, cursor: "pointer",
                background: mode === m ? "#fff" : "transparent",
                color:      mode === m ? "#6366f1" : "#6b7280",
                boxShadow:  mode === m ? "0 1px 4px rgba(0,0,0,0.08)" : "none",
              }}>
              {m === "login" ? "Sign In" : "Create Account"}
            </button>
          ))}
        </div>

        {/* Fields */}
        {mode === "register" && (
          <>
            <label style={lbl}>Full Name</label>
            <input style={inp} placeholder="Mayur Lohar" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} />
            <label style={lbl}>Company Name</label>
            <input style={inp} placeholder="Acme Pvt Ltd" value={form.company_name} onChange={e => setForm({ ...form, company_name: e.target.value })} />
          </>
        )}

        <label style={lbl}>Work Email</label>
        <input style={inp} type="email" placeholder="you@company.com" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} />

        <label style={lbl}>Password {mode === "register" && <span style={{ color: "#9ca3af", fontWeight: 400 }}>(min 8 chars, 1 uppercase, 1 number)</span>}</label>
        <input style={{ ...inp, marginBottom: 20 }} type="password" placeholder="••••••••" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })}
          onKeyDown={e => e.key === "Enter" && handleSubmit()} />

        {error && (
          <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, padding: "10px 12px", marginBottom: 16, fontSize: 13, color: "#991b1b" }}>
            {error}
          </div>
        )}

        <button onClick={handleSubmit} disabled={loading}
          style={{ width: "100%", padding: 12, background: loading ? "#c7d2fe" : "#6366f1", color: "#fff", border: "none", borderRadius: 8, fontWeight: 700, fontSize: 15, cursor: loading ? "not-allowed" : "pointer" }}>
          {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
        </button>

        {mode === "register" && (
          <p style={{ fontSize: 11, color: "#9ca3af", textAlign: "center", marginTop: 16, lineHeight: 1.6 }}>
            By creating an account you agree to our Terms of Service.<br />
            Your company data is completely isolated from other companies.
          </p>
        )}

        {/* Demo credentials hint */}
        {mode === "login" && (
          <div style={{ marginTop: 20, padding: "10px 12px", background: "#f9fafb", borderRadius: 8, fontSize: 12, color: "#6b7280", textAlign: "center" }}>
            No account? Switch to Create Account to register free.
          </div>
        )}
      </div>
    </div>
  )
}