"use client"

import { useState, useEffect, useCallback, useRef } from "react"

const STAGES = ["applied","screening","interview","offer","hired","rejected"]
const STAGE_COLORS: Record<string,{bg:string,text:string,border:string}> = {
  applied:   {bg:"#eef2ff",text:"#4338ca",border:"#c7d2fe"},
  screening: {bg:"#fffbeb",text:"#b45309",border:"#fde68a"},
  interview: {bg:"#eff6ff",text:"#1d4ed8",border:"#bfdbfe"},
  offer:     {bg:"#f5f3ff",text:"#6d28d9",border:"#ddd6fe"},
  hired:     {bg:"#ecfdf5",text:"#065f46",border:"#a7f3d0"},
  rejected:  {bg:"#fef2f2",text:"#991b1b",border:"#fecaca"},
}

const MOCK_BOARD: Record<string,any[]> = {
  applied:   [{application_id:"a1",candidate_id:"c1",name:"Priya Sharma",email:"priya@email.com",experience_years:4,skills:["Python","FastAPI","Docker"],score_total:0,screened:false,strengths:[],gaps:[],reasoning:""}],
  screening: [{application_id:"a2",candidate_id:"c2",name:"Rahul Desai",email:"rahul@email.com",experience_years:6,skills:["Python","AWS","Kubernetes"],score_total:87,score_skills:90,score_experience:85,score_relevance:86,screened:true,strengths:["Strong AWS expertise","Kubernetes in production"],gaps:["No gRPC experience"],reasoning:"Excellent match."}],
  interview: [{application_id:"a3",candidate_id:"c3",name:"Anjali Menon",email:"anjali@email.com",experience_years:5,skills:["Python","FastAPI","PostgreSQL","Redis"],score_total:92,score_skills:94,score_experience:90,score_relevance:92,screened:true,strengths:["Direct FastAPI experience","PostgreSQL at scale"],gaps:["Limited ML experience"],reasoning:"Outstanding technical fit."}],
  offer:[],hired:[],rejected:[],
}

function getToken() { return typeof window!=="undefined" ? localStorage.getItem("hr_token") : null }

async function apiCall(url:string, options:RequestInit={}) {
  const token = getToken()
  const res = await fetch(url, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : {"Content-Type":"application/json"}),
      "Authorization": `Bearer ${token}`,
      ...(options.headers||{}),
    },
  })
  if (res.status===402) {
    const data = await res.json()
    alert(`Access blocked: ${data.detail}\n\nContact us to upgrade.`)
    return null
  }
  if (res.status===401) {
    localStorage.clear()
    document.cookie="hr_token=;path=/;max-age=0"
    window.location.href="/auth"
    return null
  }
  return res
}

function ScoreBar({label,value,color="#6366f1"}:{label:string,value:number,color?:string}) {
  if(!value && value!==0) return null
  return (
    <div style={{marginBottom:6}}>
      <div style={{display:"flex",justifyContent:"space-between",fontSize:11,color:"#6b7280",marginBottom:2}}>
        <span>{label}</span><span style={{fontWeight:600,color}}>{value}</span>
      </div>
      <div style={{height:4,background:"#f3f4f6",borderRadius:2,overflow:"hidden"}}>
        <div style={{width:`${value}%`,height:"100%",background:color,borderRadius:2}}/>
      </div>
    </div>
  )
}

function CandidateCard({card,isDragging,onDragStart}:{card:any,isDragging:boolean,onDragStart:(e:any,card:any)=>void}) {
  const [expanded,setExpanded]=useState(false)
  return (
    <div draggable onDragStart={e=>onDragStart(e,card)} style={{background:"#fff",border:"1px solid #e5e7eb",borderRadius:10,padding:"12px 14px",marginBottom:8,cursor:"grab",opacity:isDragging?0.5:1,boxShadow:"0 1px 3px rgba(0,0,0,0.06)"}}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:6}}>
        <div>
          <div style={{fontWeight:600,fontSize:14,color:"#111827"}}>{card.name}</div>
          <div style={{fontSize:11,color:"#9ca3af"}}>{card.experience_years}y exp · {card.email}</div>
        </div>
        {card.screened
          ? <div style={{background:card.score_total>=80?"#ecfdf5":card.score_total>=60?"#fffbeb":"#fef2f2",color:card.score_total>=80?"#065f46":card.score_total>=60?"#92400e":"#991b1b",borderRadius:20,padding:"2px 8px",fontSize:12,fontWeight:700}}>{card.score_total}</div>
          : <div style={{fontSize:10,color:"#9ca3af",background:"#f9fafb",padding:"2px 7px",borderRadius:10}}>Screening...</div>
        }
      </div>
      <div style={{display:"flex",flexWrap:"wrap",gap:4,marginBottom:card.screened?8:0}}>
        {(card.skills||[]).slice(0,4).map((s:string)=>(
          <span key={s} style={{fontSize:10,background:"#f3f4f6",color:"#374151",padding:"2px 6px",borderRadius:4}}>{s}</span>
        ))}
      </div>
      {card.screened && (
        <>
          <div onClick={()=>setExpanded(!expanded)} style={{fontSize:11,color:"#6366f1",cursor:"pointer",userSelect:"none"}}>
            {expanded?"Hide scores":"View scores"}
          </div>
          {expanded && (
            <div style={{borderTop:"1px solid #f3f4f6",paddingTop:8,marginTop:6}}>
              <ScoreBar label="Skills match" value={card.score_skills} color="#6366f1"/>
              <ScoreBar label="Experience" value={card.score_experience} color="#3b82f6"/>
              <ScoreBar label="Role relevance" value={card.score_relevance} color="#8b5cf6"/>
              {card.reasoning && <p style={{fontSize:11,color:"#6b7280",margin:"8px 0 4px",lineHeight:1.5}}>{card.reasoning}</p>}
              {(card.strengths||[]).map((s:string,i:number)=><div key={i} style={{fontSize:10,color:"#065f46",background:"#ecfdf5",padding:"2px 6px",borderRadius:4,marginBottom:2}}>+ {s}</div>)}
              {(card.gaps||[]).map((g:string,i:number)=><div key={i} style={{fontSize:10,color:"#991b1b",background:"#fef2f2",padding:"2px 6px",borderRadius:4,marginBottom:2}}>- {g}</div>)}
            </div>
          )}
        </>
      )}
    </div>
  )
}

function PipelineBoard({jobId}:{jobId?:string}) {
  const [board,setBoard]     = useState(MOCK_BOARD)
  const [dragging,setDragging] = useState<any>(null)
  const [dragOver,setDragOver] = useState<string|null>(null)

  useEffect(()=>{
    if(!jobId) return
    const token = getToken()
    fetch(`/api/v1/pipeline/${jobId}/board`,{headers:{"Authorization":`Bearer ${token}`}})
      .then(r=>r.json())
      .then(data=>{
        if(data.columns){
          const nb:Record<string,any[]>={}
          data.columns.forEach((col:any)=>{ nb[col.stage]=col.cards||[] })
          setBoard(nb)
        }
      })
      .catch(()=>{})
  },[jobId])

  return (
    <div style={{display:"flex",gap:12,overflowX:"auto",padding:"4px 0 16px"}}>
      {STAGES.map(stage=>{
        const col=STAGE_COLORS[stage]
        const cards=board[stage]||[]
        const isOver=dragOver===stage
        return (
          <div key={stage}
            onDragOver={e=>{e.preventDefault();setDragOver(stage)}}
            onDragLeave={()=>setDragOver(null)}
            onDrop={e=>{
              e.preventDefault()
              if(!dragging)return
              setBoard(prev=>{
                const next:Record<string,any[]>={}
                STAGES.forEach(s=>{next[s]=prev[s].filter((c:any)=>c.application_id!==dragging.application_id)})
                next[stage]=[{...dragging,stage},...next[stage]]
                return next
              })
              setDragging(null);setDragOver(null)
            }}
            style={{minWidth:230,maxWidth:230,background:isOver?"#f0f4ff":"#f9fafb",border:`1.5px dashed ${isOver?"#6366f1":"#e5e7eb"}`,borderRadius:12,padding:"10px 10px 4px"}}
          >
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10}}>
              <span style={{fontSize:11,fontWeight:700,textTransform:"uppercase",letterSpacing:"0.05em",background:col.bg,color:col.text,border:`1px solid ${col.border}`,padding:"2px 8px",borderRadius:20}}>{stage}</span>
              <span style={{fontSize:11,color:"#9ca3af",fontWeight:600}}>{cards.length}</span>
            </div>
            {cards.map((card:any)=>(
              <CandidateCard key={card.application_id} card={card} isDragging={dragging?.application_id===card.application_id} onDragStart={(e,c)=>setDragging(c)}/>
            ))}
            {cards.length===0 && <div style={{textAlign:"center",padding:"20px 0",color:"#d1d5db",fontSize:12}}>Drop here</div>}
          </div>
        )
      })}
    </div>
  )
}

function JDWriter({onJobCreated}:{onJobCreated?:(id:string)=>void}) {
  const [form,setForm]=useState({title:"",department:"",location:"",employment_type:"full-time",experience_min:2,experience_max:6,skills:"",salary_min:"",salary_max:"",additional_context:""})
  const [result,setResult]=useState<any>(null)
  const [loading,setLoading]=useState(false)
  const [error,setError]=useState("")

  const handleGenerate=async()=>{
    if(!form.title||!form.department||!form.skills){setError("Title, department and skills are required");return}
    setError("");setLoading(true);setResult(null)
    try {
      const res = await apiCall("/api/v1/jobs/generate",{
        method:"POST",
        body:JSON.stringify({
          ...form,
          skills:form.skills.split(",").map((s:string)=>s.trim()).filter(Boolean),
          experience_min:Number(form.experience_min),
          experience_max:Number(form.experience_max),
          salary_min:form.salary_min?Number(form.salary_min):null,
          salary_max:form.salary_max?Number(form.salary_max):null,
        })
      })
      if(!res){setLoading(false);return}
      if(!res.ok){throw new Error(`${res.status}`)}
      const data = await res.json()
      setResult(data)
      if(data.job?.id && onJobCreated) onJobCreated(data.job.id)
    } catch(e){
      setError("Could not reach API. Is the backend running?")
    }
    setLoading(false)
  }

  const inp={width:"100%",padding:"8px 10px",border:"1px solid #e5e7eb",borderRadius:7,fontSize:13,color:"#111827",background:"#fff",outline:"none",boxSizing:"border-box" as const}
  const lbl={fontSize:12,fontWeight:600,color:"#374151",display:"block",marginBottom:4}

  return (
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:24,alignItems:"start"}}>
      <div style={{background:"#fff",border:"1px solid #e5e7eb",borderRadius:12,padding:20}}>
        <h3 style={{margin:"0 0 16px",fontSize:15,fontWeight:700,color:"#111827"}}>AI Job Description Writer</h3>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10,marginBottom:10}}>
          {[["Job Title *","title","Senior Backend Engineer"],["Department *","department","Engineering"],["Location","location","Pune / Remote"]].map(([label,key,ph])=>(
            <div key={key}><label style={lbl}>{label}</label><input style={inp} placeholder={ph} value={(form as any)[key]} onChange={e=>setForm({...form,[key]:e.target.value})}/></div>
          ))}
          <div><label style={lbl}>Employment Type</label>
            <select style={inp} value={form.employment_type} onChange={e=>setForm({...form,employment_type:e.target.value})}>
              <option value="full-time">Full-time</option><option value="contract">Contract</option><option value="part-time">Part-time</option><option value="internship">Internship</option>
            </select>
          </div>
          <div><label style={lbl}>Min Experience (yr)</label><input style={inp} type="number" value={form.experience_min} onChange={e=>setForm({...form,experience_min:Number(e.target.value)})}/></div>
          <div><label style={lbl}>Max Experience (yr)</label><input style={inp} type="number" value={form.experience_max} onChange={e=>setForm({...form,experience_max:Number(e.target.value)})}/></div>
          <div><label style={lbl}>Salary Min</label><input style={inp} placeholder="800000" value={form.salary_min} onChange={e=>setForm({...form,salary_min:e.target.value})}/></div>
          <div><label style={lbl}>Salary Max</label><input style={inp} placeholder="1500000" value={form.salary_max} onChange={e=>setForm({...form,salary_max:e.target.value})}/></div>
        </div>
        <div style={{marginBottom:10}}><label style={lbl}>Required Skills * (comma-separated)</label><input style={inp} placeholder="Python, FastAPI, PostgreSQL" value={form.skills} onChange={e=>setForm({...form,skills:e.target.value})}/></div>
        <div style={{marginBottom:16}}><label style={lbl}>Additional Context</label><textarea style={{...inp,height:60,resize:"vertical"}} value={form.additional_context} onChange={e=>setForm({...form,additional_context:e.target.value})}/></div>
        {error && <p style={{color:"#ef4444",fontSize:12,marginBottom:8}}>{error}</p>}
        <button onClick={handleGenerate} disabled={loading} style={{width:"100%",padding:10,background:loading?"#c7d2fe":"#6366f1",color:"#fff",border:"none",borderRadius:8,fontWeight:700,fontSize:14,cursor:loading?"not-allowed":"pointer"}}>
          {loading?"Generating JD...":"Generate Job Description"}
        </button>
      </div>
      <div>
        {!result && <div style={{background:"#f9fafb",border:"1.5px dashed #e5e7eb",borderRadius:12,padding:32,textAlign:"center",color:"#9ca3af"}}><p style={{margin:0,fontSize:13}}>Fill the form and click generate.</p></div>}
        {result && (
          <div style={{background:"#fff",border:"1px solid #e5e7eb",borderRadius:12,padding:20,maxHeight:600,overflowY:"auto"}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:14}}>
              <h3 style={{margin:0,fontSize:15,fontWeight:700,color:"#111827"}}>{result.job.title}</h3>
              <span style={{fontSize:11,background:"#ecfdf5",color:"#065f46",padding:"2px 8px",borderRadius:10,fontWeight:600}}>Saved</span>
            </div>
            {result.job.bias_flags?.length===0 && <div style={{background:"#ecfdf5",border:"1px solid #a7f3d0",borderRadius:8,padding:"6px 12px",marginBottom:12,fontSize:12,color:"#065f46",fontWeight:600}}>No bias patterns detected</div>}
            <div style={{fontSize:13,color:"#374151",lineHeight:1.7,whiteSpace:"pre-wrap",marginBottom:14}}>{result.job.description}</div>
            {result.ai_extras?.what_we_offer?.length>0 && (
              <div style={{borderTop:"1px solid #f3f4f6",paddingTop:12}}>
                <div style={{fontSize:12,fontWeight:700,color:"#6b7280",marginBottom:6}}>BENEFITS</div>
                {result.ai_extras.what_we_offer.map((b:string,i:number)=><div key={i} style={{fontSize:12,color:"#374151",marginBottom:3}}>- {b}</div>)}
              </div>
            )}
            <div style={{marginTop:12,display:"flex",gap:8}}>
              <button style={{flex:1,padding:7,background:"#6366f1",color:"#fff",border:"none",borderRadius:7,fontSize:12,fontWeight:600,cursor:"pointer"}}>Publish Job</button>
              <button onClick={()=>navigator.clipboard?.writeText(result.job.description)} style={{flex:1,padding:7,background:"#f9fafb",color:"#374151",border:"1px solid #e5e7eb",borderRadius:7,fontSize:12,cursor:"pointer"}}>Copy JD</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

function ResumeScreener({initialJobId=""}:{initialJobId?:string}) {
  const [jobId,setJobId]     = useState(initialJobId)
  const [files,setFiles]     = useState<File[]>([])
  const [results,setResults] = useState<any[]>([])
  const [screening,setScreening] = useState(false)
  const [dragOver,setDragOver]   = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(()=>{ if(initialJobId) setJobId(initialJobId) },[initialJobId])

  const handleDrop=useCallback((e:React.DragEvent)=>{
    e.preventDefault();setDragOver(false)
    setFiles(prev=>[...prev,...Array.from(e.dataTransfer.files).filter(f=>f.name.endsWith(".pdf"))])
  },[])

  const handleScreen = async () => {
    if(!jobId){alert("Enter a Job ID first");return}
    setScreening(true)
    const formData = new FormData()
    for(const f of files) formData.append("files", f)
    try {
      const token = getToken()

      // Upload directly to backend — bypass Next.js proxy for file uploads
      const res = await fetch(`http://localhost:8000/api/v1/candidates/bulk-upload/${jobId}`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData,
      })
      if(!res.ok){ alert("Upload failed: " + res.status); setScreening(false); return }
      await res.json()

      await new Promise(r => setTimeout(r, 3000))

    // Ranked results can go through proxy normally
      const ranked = await apiCall(`/api/v1/candidates/${jobId}/ranked`)
      if(!ranked){ setScreening(false); return }
      setResults(await ranked.json())
    } catch(e){
      alert("API error. Is backend running?")
    }
    setScreening(false)
  }

  return (
    <div style={{display:"grid",gridTemplateColumns:"320px 1fr",gap:20,alignItems:"start"}}>
      <div>
        <div style={{background:"#fff",border:"1px solid #e5e7eb",borderRadius:12,padding:16,marginBottom:12}}>
          <label style={{fontSize:12,fontWeight:600,color:"#374151",display:"block",marginBottom:4}}>Job ID</label>
          <input style={{width:"100%",padding:"7px 10px",border:"1px solid #e5e7eb",borderRadius:7,fontSize:13,boxSizing:"border-box"}} value={jobId} onChange={e=>setJobId(e.target.value)} placeholder="Auto-filled after JD generation"/>
        </div>
        <div onDrop={handleDrop} onDragOver={e=>{e.preventDefault();setDragOver(true)}} onDragLeave={()=>setDragOver(false)} onClick={()=>fileRef.current?.click()}
          style={{border:`2px dashed ${dragOver?"#6366f1":"#d1d5db"}`,borderRadius:12,padding:"28px 20px",textAlign:"center",background:dragOver?"#eef2ff":"#fafafa",cursor:"pointer",marginBottom:12}}>
          <div style={{fontSize:28,marginBottom:8}}>PDF</div>
          <div style={{fontSize:13,color:"#374151",fontWeight:600}}>Drop PDF resumes here</div>
          <div style={{fontSize:11,color:"#9ca3af",marginTop:4}}>or click to browse</div>
          <input ref={fileRef} type="file" accept=".pdf" multiple onChange={e=>setFiles(prev=>[...prev,...Array.from(e.target.files||[])])} style={{display:"none"}}/>
        </div>
        {files.length>0 && (
          <div style={{background:"#fff",border:"1px solid #e5e7eb",borderRadius:10,padding:12,marginBottom:12}}>
            {files.slice(0,5).map((f,i)=>(
              <div key={i} style={{display:"flex",justifyContent:"space-between",fontSize:12,color:"#374151",padding:"3px 0"}}>
                <span>{f.name.slice(0,24)}</span><span style={{color:"#9ca3af"}}>{(f.size/1024).toFixed(0)}kb</span>
              </div>
            ))}
          </div>
        )}
        <button onClick={handleScreen} disabled={screening} style={{width:"100%",padding:10,background:screening?"#c7d2fe":"#6366f1",color:"#fff",border:"none",borderRadius:8,fontWeight:700,fontSize:14,cursor:screening?"not-allowed":"pointer"}}>
          {screening?"Screening...":files.length?`Screen ${files.length} Resumes`:"Upload resumes first"}
        </button>
      </div>
      <div>
        {!results.length && !screening && <div style={{background:"#f9fafb",border:"1.5px dashed #e5e7eb",borderRadius:12,padding:40,textAlign:"center",color:"#9ca3af"}}><p style={{margin:0,fontSize:13}}>Upload resumes and click Screen.</p></div>}
        {screening && <div style={{background:"#f9fafb",border:"1px solid #e5e7eb",borderRadius:12,padding:32,textAlign:"center"}}><div style={{fontSize:13,color:"#6366f1",fontWeight:600}}>Analyzing resumes...</div></div>}
        {results.length>0 && (
          <div>
            <div style={{fontSize:12,color:"#6b7280",marginBottom:10,fontWeight:600}}>{results.length} CANDIDATES - RANKED BY SCORE</div>
            {results.map((r:any,i:number)=>(
              <div key={i} style={{background:"#fff",border:"1px solid #e5e7eb",borderRadius:10,padding:"12px 16px",marginBottom:10,borderLeft:`3px solid ${r.scores?.total>=80?"#10b981":r.scores?.total>=60?"#f59e0b":"#ef4444"}`}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:8}}>
                  <div>
                    <div style={{display:"flex",alignItems:"center",gap:8}}>
                      <span style={{fontSize:11,color:"#9ca3af",fontWeight:700}}>#{i+1}</span>
                      <span style={{fontWeight:700,fontSize:14,color:"#111827"}}>{r.name}</span>
                    </div>
                    <div style={{fontSize:11,color:"#9ca3af",marginTop:2}}>{r.email} - {r.experience_years}y exp</div>
                  </div>
                  <div style={{fontSize:22,fontWeight:800,color:r.scores?.total>=80?"#10b981":r.scores?.total>=60?"#f59e0b":"#ef4444"}}>{r.scores?.total}</div>
                </div>
                <div style={{display:"flex",gap:4,flexWrap:"wrap",marginBottom:8}}>
                  {(r.skills||[]).slice(0,5).map((s:string)=><span key={s} style={{fontSize:10,background:"#f3f4f6",color:"#374151",padding:"2px 6px",borderRadius:4}}>{s}</span>)}
                </div>
                <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:8}}>
                  <ScoreBar label="Skills" value={r.scores?.skills} color="#6366f1"/>
                  <ScoreBar label="Experience" value={r.scores?.experience} color="#3b82f6"/>
                  <ScoreBar label="Relevance" value={r.scores?.relevance} color="#8b5cf6"/>
                </div>
                {r.reasoning && <p style={{fontSize:11,color:"#6b7280",margin:"8px 0 0",lineHeight:1.5}}>{r.reasoning}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default function HRAgent() {
  const [tab,setTab]               = useState("jd")
  const [lastJobId,setLastJobId]   = useState("")
  const [user,setUser]             = useState<{full_name?:string}>({})
  const [company,setCompany]       = useState<{name?:string}>({})

  useEffect(()=>{
    try{setUser(JSON.parse(localStorage.getItem("hr_user")||"{}"))}catch{}
    try{setCompany(JSON.parse(localStorage.getItem("hr_company")||"{}"))}catch{}
  },[])

  const tabs=[
    {id:"jd",       label:"JD Writer",       icon:"✦"},
    {id:"screener", label:"Resume Screener", icon:">"},
    {id:"pipeline", label:"Pipeline",        icon:"="},
  ]

  return (
    <div style={{minHeight:"100vh",background:"#f8f9fc",fontFamily:"system-ui,sans-serif"}}>
      <div style={{background:"#fff",borderBottom:"1px solid #e5e7eb",padding:"0 24px"}}>
        <div style={{maxWidth:1200,margin:"0 auto",display:"flex",alignItems:"center",justifyContent:"space-between",height:56}}>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            <div style={{width:32,height:32,background:"#6366f1",borderRadius:8,display:"flex",alignItems:"center",justifyContent:"center",color:"#fff",fontSize:16}}>H</div>
            <span style={{fontWeight:800,fontSize:16,color:"#111827"}}>HireAgent</span>
            <span style={{fontSize:11,background:"#f3f4f6",color:"#6b7280",padding:"2px 7px",borderRadius:10}}>Beta</span>
          </div>
          <div style={{display:"flex",alignItems:"center",gap:12}}>
            <div style={{textAlign:"right"}}>
              <div style={{fontSize:12,fontWeight:600,color:"#374151"}}>{user.full_name||""}</div>
              <div style={{fontSize:11,color:"#9ca3af"}}>{company.name||""}</div>
            </div>
            <button onClick={()=>{localStorage.clear();document.cookie="hr_token=;path=/;max-age=0";window.location.href="/auth"}}
              style={{fontSize:12,color:"#6b7280",background:"none",border:"1px solid #e5e7eb",borderRadius:6,padding:"4px 10px",cursor:"pointer"}}>
              Logout
            </button>
          </div>
        </div>
      </div>
      <div style={{background:"#fff",borderBottom:"1px solid #e5e7eb"}}>
        <div style={{maxWidth:1200,margin:"0 auto",padding:"0 24px",display:"flex"}}>
          {tabs.map(t=>(
            <button key={t.id} onClick={()=>setTab(t.id)} style={{padding:"14px 20px",border:"none",background:"transparent",fontSize:13,fontWeight:tab===t.id?700:500,color:tab===t.id?"#6366f1":"#6b7280",borderBottom:tab===t.id?"2px solid #6366f1":"2px solid transparent",cursor:"pointer"}}>
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </div>
      <div style={{maxWidth:1200,margin:"24px auto",padding:"0 24px"}}>
        {tab==="jd"       && <JDWriter onJobCreated={setLastJobId}/>}
        {tab==="screener" && <ResumeScreener initialJobId={lastJobId}/>}
        {tab==="pipeline" && (
          <div>
            <h2 style={{margin:"0 0 4px",fontSize:16,fontWeight:700,color:"#111827"}}>Candidate Pipeline</h2>
            {lastJobId
              ? <p style={{margin:"0 0 16px",fontSize:12,color:"#9ca3af"}}>Showing real candidates for job: {lastJobId}</p>
              : <p style={{margin:"0 0 16px",fontSize:12,color:"#9ca3af"}}>Generate a job first to see real candidates. Showing demo data.</p>
            }
            <PipelineBoard jobId={lastJobId}/>
          </div>
        )}
      </div>
    </div>
  )
}