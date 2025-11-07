"use client"
import React, { useEffect, useState } from 'react'

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

type Metrics = { [k: string]: number }

export default function EvalPage() {
  const [k, setK] = useState(10)
  const [metrics, setMetrics] = useState<{mode: string; data: Metrics}[]>([])

  async function run() {
    const modes = ['baseline','embed','hybrid']
    const res = await Promise.all(modes.map(async m => {
      const r = await fetch(`${API_BASE}/eval/offline?mode=${m}&k=${k}`)
      const d = await r.json()
      return { mode: m, data: d }
    }))
    setMetrics(res)
  }

  useEffect(() => { run() }, [])

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Offline Evaluation</h2>
      <div className="flex gap-2 items-center">
        <span className="text-sm">K</span>
        <select className="border rounded px-2 py-1" value={k} onChange={e=>setK(parseInt(e.target.value))}>
          <option value={5}>5</option>
          <option value={10}>10</option>
        </select>
        <button className="border rounded px-2 py-1" onClick={run}>Run</button>
      </div>
      <div className="grid grid-cols-1 gap-3">
        {metrics.map(m => (
          <div key={m.mode} className="border rounded p-3">
            <div className="font-medium mb-1">{m.mode.toUpperCase()}</div>
            <div className="text-sm">precision@k: {m.data['precision@k']?.toFixed(3)}</div>
            <div className="text-sm">recall@k: {m.data['recall@k']?.toFixed(3)}</div>
            <div className="text-sm">ndcg@k: {m.data['ndcg@k']?.toFixed(3)}</div>
          </div>
        ))}
      </div>
    </div>
  )
}


