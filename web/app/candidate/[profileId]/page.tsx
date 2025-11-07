"use client"
import React, { useEffect, useMemo, useState } from 'react'
import { useParams } from 'next/navigation'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type Rec = { job_id: string; title: string; experience_level?: string; score: number; breakdown: { embed: number; skill: number; exp: number; kw: number } }

export default function CandidatePage() {
  const params = useParams() as { profileId: string }
  const [mode, setMode] = useState<'baseline'|'embed'|'hybrid'>('hybrid')
  const [recs, setRecs] = useState<Rec[]>([])
  const [loading, setLoading] = useState(false)
  const [gapFor, setGapFor] = useState<string | null>(null)
  const [gapData, setGapData] = useState<any>(null)

  useEffect(() => {
    async function fetchRecs() {
      setLoading(true)
      try {
        let url = `${API_BASE}/recommend/by_profile?profile_id=${params.profileId}&k=10&mode=${mode}`
        if (params.profileId.startsWith('dataset-')) {
          const rid = params.profileId.replace('dataset-','')
          url = `${API_BASE}/recommend/by_resume_id?resume_id=${rid}&k=10&mode=${mode}`
        }
        const r = await fetch(url)
        const d = await r.json()
        setRecs(d.results || [])
      } finally { setLoading(false) }
    }
    fetchRecs()
  }, [params.profileId, mode])

  async function openGaps(jobId: string) {
    setGapFor(jobId)
    let url = `${API_BASE}/gaps?profile_id=${params.profileId}&job_id=${jobId}`
    if (params.profileId.startsWith('dataset-')) {
      const rid = params.profileId.replace('dataset-','')
      url = `${API_BASE}/gaps?resume_id=${rid}&job_id=${jobId}`
    }
    const r = await fetch(url)
    const d = await r.json()
    setGapData(d)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Recommendations</h2>
        <div className="flex gap-2 items-center">
          <span className="text-sm">Mode</span>
          <select className="border rounded px-2 py-1" value={mode} onChange={e=>setMode(e.target.value as any)}>
            <option value="baseline">Baseline</option>
            <option value="embed">Embedding</option>
            <option value="hybrid">Hybrid</option>
          </select>
        </div>
      </div>
      {loading && <div className="text-sm">Loading...</div>}
      <div className="grid grid-cols-1 gap-3">
        {recs.map(r => {
          const jobId = String((r as any).job_id ?? (r as any).jobId ?? '')
          return (
          <div key={jobId || r.title} className="border rounded p-3">
            <div className="flex justify-between">
              <div>
                <div className="font-medium">{r.title}</div>
                <div className="text-xs text-neutral-600">{r.experience_level || ''}</div>
              </div>
              <div className="text-right">
                <div className="text-sm">Score: {(r.score).toFixed(3)}</div>
                <div className="text-[11px] text-neutral-600">embed {r.breakdown.embed.toFixed(2)} | skill {r.breakdown.skill.toFixed(2)} | exp {r.breakdown.exp.toFixed(2)} | kw {r.breakdown.kw.toFixed(2)}</div>
              </div>
            </div>
            <div className="mt-2 flex gap-2">
              <button className="border rounded px-2 py-1" onClick={()=> jobId ? openGaps(jobId) : alert('Unable to open gaps: missing job id')}>View Gaps</button>
              <button className="border rounded px-2 py-1">Looks Good</button>
              <button className="border rounded px-2 py-1">Not Relevant</button>
            </div>
          </div>
        )})}
      </div>
      {gapFor && gapData && (
        <div className="fixed inset-0 bg-black/40 flex">
          <div className="ml-auto w-full max-w-xl h-full bg-white p-4 overflow-y-auto">
            <div className="flex justify-between items-center mb-2">
              <div className="font-medium">Skill Gaps</div>
              <button className="border rounded px-2 py-1" onClick={()=>{setGapFor(null); setGapData(null)}}>Close</button>
            </div>
            <div className="space-y-3">
              <div>
                <div className="text-sm font-medium">Present</div>
                <div className="flex gap-1 flex-wrap">{(gapData.present||[]).slice(0,20).map((s:string)=>(<span key={s} className="px-2 py-0.5 text-xs border rounded">{s}</span>))}</div>
              </div>
              <div>
                <div className="text-sm font-medium">Missing</div>
                <div className="flex gap-1 flex-wrap">{(gapData.missing||[]).map((s:string)=>(<span key={s} className="px-2 py-0.5 text-xs border rounded bg-red-50">{s}</span>))}</div>
              </div>
              <div>
                <div className="text-sm font-medium">Weak</div>
                <div className="flex gap-1 flex-wrap">{(gapData.weak||[]).map((s:string)=>(<span key={s} className="px-2 py-0.5 text-xs border rounded bg-yellow-50">{s}</span>))}</div>
              </div>
              <div>
                <div className="text-sm font-medium">Suggestions</div>
                <div className="space-y-2">
                  {Object.entries(gapData.suggestions||{}).map(([skill, courses]: any)=> (
                    <div key={skill}>
                      <div className="text-sm font-medium">{skill}</div>
                      <ul className="list-disc pl-5 text-sm">
                        {courses.map((c:any, i:number)=>(<li key={i}>{c.course_name} — {c.provider} ({c.hours}h)</li>))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div className="text-sm font-medium">3-Month Roadmap</div>
                <pre className="text-xs whitespace-pre-wrap bg-neutral-50 p-2 rounded border">{gapData.roadmap_3mo}</pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}


