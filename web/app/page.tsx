"use client"
import React, { useState, useEffect } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type Candidate = { resume_id: string; summary: string }

export default function HomePage() {
  const [tab, setTab] = useState<'paste'|'upload'|'dataset'>('paste')
  const [text, setText] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [persona, setPersona] = useState('Fresh Grad')
  const [loading, setLoading] = useState(false)
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch(`${API_BASE}/candidates`).then(r => r.json()).then(d => setCandidates(d.candidates || [])).catch(() => {})
  }, [])

  async function analyzeAndGo() {
    setError(null)
    setLoading(true)
    try {
      const form = new FormData()
      if (text) form.append('text', text)
      form.append('persona', persona)
      if (file) form.append('file', file)
      const res = await fetch(`${API_BASE}/profile/analyze`, { method: 'POST', body: form })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Analyze failed')
      window.location.href = `/candidate/${data.profile_id}`
    } catch (e: any) {
      setError(e.message)
    } finally { setLoading(false) }
  }

  async function pickCandidate(id: string) {
    // for demo, we ask API to recommend by resume_id and synthesize a profile via redirect param
    // We'll create a profile by posting text extracted from dataset via backend endpoint in later enhancement
    window.location.href = `/candidate/dataset-${id}`
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">AI Job Recommender</h1>
      <div className="flex gap-2 items-center">
        <label className="text-sm">Persona</label>
        <select className="border rounded px-2 py-1" value={persona} onChange={e => setPersona(e.target.value)}>
          <option>Fresh Grad</option>
          <option>Mid-Career Switcher</option>
          <option>Job-Seeker Retraining</option>
        </select>
      </div>
      <div className="flex gap-2">
        <button className={`px-3 py-1 rounded ${tab==='paste'?'bg-black text-white':'border'}`} onClick={()=>setTab('paste')}>Paste Profile</button>
        <button className={`px-3 py-1 rounded ${tab==='upload'?'bg-black text-white':'border'}`} onClick={()=>setTab('upload')}>Upload Resume</button>
        <button className={`px-3 py-1 rounded ${tab==='dataset'?'bg-black text-white':'border'}`} onClick={()=>setTab('dataset')}>Pick from Dataset</button>
      </div>
      {tab==='paste' && (
        <textarea className="w-full h-48 border rounded p-2" placeholder="Paste resume/profile text" value={text} onChange={e=>setText(e.target.value)} />
      )}
      {tab==='upload' && (
        <input type="file" accept=".pdf,.docx,.txt" onChange={e=>setFile(e.target.files?.[0] || null)} />
      )}
      {tab==='dataset' && (
        <div className="grid grid-cols-1 gap-2">
          {candidates.map(c => (
            <div key={c.resume_id} className="border rounded p-2 flex justify-between items-center">
              <div className="text-sm line-clamp-2 max-w-3xl">{c.summary || 'No summary'}</div>
              <button className="border px-2 py-1 rounded" onClick={()=>pickCandidate(c.resume_id.toString())}>Use</button>
            </div>
          ))}
          {candidates.length===0 && <div className="text-sm text-neutral-500">No dataset available.</div>}
        </div>
      )}
      {error && <div className="text-sm text-red-600">{error}</div>}
      <button disabled={loading} className="px-4 py-2 bg-blue-600 text-white rounded" onClick={analyzeAndGo}>{loading? 'Analyzing...' : 'Analyze & Recommend'}</button>
    </div>
  )}


