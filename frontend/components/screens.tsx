'use client'
import { FormEvent, ReactNode, useEffect, useMemo, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api, ApiList, login } from '@/lib/api'

type Dashboard = { metrics: Record<string, number>; monthly_fuel: any[]; monthly_maintenance: any[]; utilization: any[]; fuel_efficiency: any[]; route_trips: any[]; alerts: any[]; insurance_alerts: any[] }
export const nav = ['Dashboard', 'Vehicles', 'Drivers', 'Trips', 'Fuel', 'Maintenance', 'Accidents', 'Insurance', 'Expenses', 'Insights']
export const pageEndpoint: Record<string,string> = { Vehicles:'/vehicles', Drivers:'/drivers', Trips:'/trips', Fuel:'/fuel', Maintenance:'/maintenance', Accidents:'/accidents', Insurance:'/insurance', Expenses:'/expenses' }
const labels: Record<string,string> = { total_vehicles:'Total vehicles', active_vehicles:'Active vehicles', vehicles_under_maintenance:'In maintenance', active_drivers:'Active drivers', completed_trips:'Completed trips', total_fuel_cost:'Fuel expenditure', total_maintenance_cost:'Maintenance expenditure', total_operating_cost:'Operating cost' }
const colors = ['#1a936f','#0ea5e9','#f59e0b','#8b5cf6','#ef4444','#14b8a6','#64748b','#ec4899']
function money(value: unknown) { return `₹${Number(value || 0).toLocaleString('en-IN', {maximumFractionDigits:0})}` }

export function Login({ onSuccess }: {onSuccess: () => void}) {
  const [username,setUsername]=useState('admin'), [password,setPassword]=useState('Fleet@123'), [error,setError]=useState(''), [busy,setBusy]=useState(false)
  async function submit(e: FormEvent) { e.preventDefault(); setBusy(true); setError(''); try { const r=await login(username,password); localStorage.setItem('fleet_token',r.access_token); localStorage.setItem('fleet_role',r.role); onSuccess() } catch(e) { setError(e instanceof Error?e.message:'Login failed') } finally { setBusy(false) } }
  return <main className="min-h-screen bg-navy grid place-items-center p-6"><form onSubmit={submit} className="w-full max-w-md panel p-8 shadow-2xl"><div className="mb-8"><div className="text-brand font-bold tracking-widest text-xs">SMART FLEET</div><h1 className="mt-2 text-3xl font-bold">Operations, in view.</h1><p className="mt-2 text-slate-500">Sign in to manage your fleet and analytics.</p></div><label className="text-sm font-medium">Username<input value={username} onChange={e=>setUsername(e.target.value)} className="mt-1 w-full rounded-lg border p-3"/></label><label className="mt-4 block text-sm font-medium">Password<input type="password" value={password} onChange={e=>setPassword(e.target.value)} className="mt-1 w-full rounded-lg border p-3"/></label>{error&&<p className="mt-3 text-sm text-red-600">{error}</p>}<button disabled={busy} className="mt-6 w-full rounded-lg bg-brand py-3 font-semibold text-white hover:bg-emerald-700">{busy?'Signing in…':'Sign in'}</button><p className="mt-5 text-xs text-slate-400">Demo accounts: admin / Fleet@123, manager / Manager@123, viewer / Viewer@123</p></form></main>
}

function ChartCard({title,children}:{title:string;children:ReactNode}) { return <section className="panel p-5"><h2 className="mb-4 font-semibold">{title}</h2><div className="h-64">{children}</div></section> }
export function DashboardPage() { const [data,setData]=useState<Dashboard|null>(null),[error,setError]=useState(''); useEffect(()=>{api<Dashboard>('/analytics/dashboard').then(setData).catch(e=>setError(e.message))},[]); if(error) return <div className="panel p-6 text-red-600">Unable to load dashboard: {error}</div>; if(!data) return <div className="panel p-6 animate-pulse">Loading live fleet analytics…</div>; return <div className="space-y-6"><div><p className="text-sm font-medium text-brand">FLEET OVERVIEW</p><h1 className="text-2xl font-bold">Good morning, operations team</h1><p className="text-slate-500">Live performance from the PostgreSQL fleet database.</p></div><div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{Object.entries(data.metrics).map(([k,v])=><article key={k} className="metric"><p className="text-sm text-slate-500">{labels[k]}</p><p className="mt-2 text-2xl font-bold">{k.includes('cost')?money(v):Number(v).toLocaleString('en-IN')}</p></article>)}</div><div className="grid gap-6 xl:grid-cols-2"><ChartCard title="Monthly fuel expenditure"><ResponsiveContainer><LineChart data={data.monthly_fuel}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="month"/><YAxis/><Tooltip formatter={money}/><Line type="monotone" dataKey="value" stroke="#1a936f" strokeWidth={3}/></LineChart></ResponsiveContainer></ChartCard><ChartCard title="Maintenance expenditure"><ResponsiveContainer><BarChart data={data.monthly_maintenance}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="month"/><YAxis/><Tooltip formatter={money}/><Bar dataKey="value" fill="#f59e0b" radius={[5,5,0,0]}/></BarChart></ResponsiveContainer></ChartCard><ChartCard title="Top vehicle utilization (km)"><ResponsiveContainer><BarChart data={data.utilization} layout="vertical"><XAxis type="number"/><YAxis dataKey="name" type="category" width={95}/><Tooltip/><Bar dataKey="value" fill="#0ea5e9"/></BarChart></ResponsiveContainer></ChartCard><ChartCard title="Fuel efficiency (km/l)"><ResponsiveContainer><BarChart data={data.fuel_efficiency}><XAxis dataKey="name" hide/><YAxis/><Tooltip/><Bar dataKey="value" fill="#8b5cf6"/></BarChart></ResponsiveContainer></ChartCard></div><section className="panel overflow-hidden"><div className="flex items-center justify-between px-5 py-4"><h2 className="font-semibold">Service alerts</h2><span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800">Action needed</span></div>{data.alerts.length?<table className="w-full"><thead className="bg-slate-50"><tr><th className="table-head">Vehicle</th><th className="table-head">Status</th><th className="table-head">Service date</th><th className="table-head">Service odometer</th></tr></thead><tbody>{data.alerts.map((a:any)=><tr key={a.registration_number} className="border-t"><td className="table-cell font-medium">{a.registration_number}</td><td className="table-cell capitalize">{a.service_status.replace('_',' ')}</td><td className="table-cell">{a.next_service_date||'—'}</td><td className="table-cell">{a.next_service_odometer||'—'}</td></tr>)}</tbody></table>:<p className="p-5 text-slate-500">No maintenance alerts. Fleet is on schedule.</p>}</section></div> }

const defaultPayloads: Record<string, Record<string, unknown>> = {
  '/vehicles': { registration_number: 'KA01ZZ9001', vehicle_type_id: 1, branch_id: 1, chassis_number: 'CHS00000000009001', purchase_date: '2026-01-15', current_odometer: 0, status: 'active' },
  '/drivers': { branch_id: 1, full_name: 'Vikram Rao', license_number: 'KA0120200099001', license_expiry: '2032-05-20', joining_date: '2025-01-10', phone: '9876543299', status: 'active' },
  '/trips': { vehicle_id: 1, driver_id: 1, route_id: 1, start_time: '2026-06-15T08:00:00Z', start_odometer: 24000, status: 'planned', notes: 'Scheduled dispatch' },
  '/fuel': { vehicle_id: 1, driver_id: 1, transaction_date: '2026-06-15', fuel_type: 'Diesel', litres: 45, price_per_litre: 92.5, odometer: 24000, fuel_station: 'Indian Oil, Bengaluru' },
  '/maintenance': { vehicle_id: 1, maintenance_type_id: 1, service_center_id: 1, service_date: '2026-06-15', odometer: 24000, cost: 4500, description: 'Routine inspection' },
  '/accidents': { vehicle_id: 1, driver_id: 1, accident_date: '2026-06-15', location: 'NH-48 Tumakuru', severity: 'minor', estimated_damage: 3500, description: 'Bumper scratch' },
  '/insurance': { vehicle_id: 1, provider: 'New India Assurance', policy_number: 'POL-2026-9001', start_date: '2026-01-01', expiry_date: '2027-01-01', premium: 38000, coverage_amount: 1500000 },
  '/expenses': { vehicle_id: 1, expense_date: '2026-06-15', category: 'toll', amount: 650, description: 'FASTag highway toll' },
}

export function TablePage({title,endpoint}:{title:string;endpoint:string}) {
  const [data,setData]=useState<ApiList|null>(null),[search,setSearch]=useState(''),[error,setError]=useState('')
  const [showAdd,setShowAdd]=useState(false),[form,setForm]=useState<Record<string,unknown>>(()=>({...(defaultPayloads[endpoint]||{})})),[formErr,setFormErr]=useState(''),[saving,setSaving]=useState(false)
  const role = typeof window !== 'undefined' ? localStorage.getItem('fleet_role') || 'viewer' : 'viewer'
  const canWrite = role === 'admin' || role === 'fleet_manager'
  const canDelete = role === 'admin'
  const refresh=()=>api<ApiList>(`${endpoint}?page_size=20${search?`&search=${encodeURIComponent(search)}`:''}`).then(setData).catch(e=>setError(e.message))
  useEffect(()=>{ setForm({...(defaultPayloads[endpoint]||{})}); setShowAdd(false); setFormErr(''); refresh() },[endpoint])
  const cols=useMemo(()=>data?.items[0]?Object.keys(data.items[0]).filter(k=>!k.endsWith('_id')||k===Object.keys(data.items[0])[0]).slice(0,7):[],[data])
  const idCol = data?.items[0] ? Object.keys(data.items[0])[0] : ''
  async function createRecord(e: FormEvent) {
    e.preventDefault(); setSaving(true); setFormErr('')
    try { await api(endpoint, { method: 'POST', body: JSON.stringify(form) }); setShowAdd(false); refresh() }
    catch(err) { setFormErr(err instanceof Error ? err.message : 'Failed to create record') }
    finally { setSaving(false) }
  }
  async function removeRecord(id: unknown) {
    setError('')
    try { await api(`${endpoint}/${id}`, { method: 'DELETE' }); refresh() }
    catch(err) { setError(err instanceof Error ? err.message : 'Delete failed') }
  }
  return <div>
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div><p className="text-sm font-medium text-brand">MANAGEMENT</p><h1 className="text-2xl font-bold">{title}</h1><p className="text-slate-500">Search, create, and review records stored in PostgreSQL.</p></div>
      <div className="flex gap-2">
        {canWrite && <button onClick={()=>setShowAdd(v=>!v)} className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700">{showAdd ? 'Cancel' : `+ Add ${title.replace(/s$/,'')}`}</button>}
        <button onClick={refresh} className="rounded-lg border bg-white px-4 py-2 text-sm font-medium">Refresh</button>
      </div>
    </div>
    {showAdd && <form onSubmit={createRecord} className="panel mb-6 p-5">
      <h2 className="mb-4 font-semibold">New {title.replace(/s$/,'')} record</h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(form).map(([k,v]) => <label key={k} className="block text-xs font-medium uppercase tracking-wide text-slate-600">{k.replaceAll('_',' ')}
          <input value={String(v ?? '')} onChange={e=>setForm({...form, [k]: typeof defaultPayloads[endpoint]?.[k]==='number' ? Number(e.target.value) : e.target.value})} className="mt-1 w-full rounded-lg border px-3 py-2 text-sm normal-case text-ink"/>
        </label>)}
      </div>
      {formErr && <p className="mt-3 text-sm text-red-600">{formErr}</p>}
      <div className="mt-4 flex justify-end"><button disabled={saving} className="rounded-lg bg-navy px-5 py-2 text-sm font-semibold text-white">{saving ? 'Saving…' : 'Save to PostgreSQL'}</button></div>
    </form>}
    <div className="panel overflow-hidden"><div className="flex gap-2 border-b p-4"><input value={search} onChange={e=>setSearch(e.target.value)} onKeyDown={e=>e.key==='Enter'&&refresh()} placeholder={`Search ${title.toLowerCase()}…`} className="w-full max-w-sm rounded-lg border px-3 py-2 text-sm"/><button onClick={refresh} className="rounded-lg bg-navy px-4 text-sm font-medium text-white">Search</button></div>{error?<p className="p-5 text-red-600">{error}</p>:!data?<p className="p-5">Loading records…</p>:data.items.length===0?<p className="p-8 text-center text-slate-500">No records match this search.</p>:<div className="overflow-x-auto"><table className="min-w-full"><thead className="bg-slate-50"><tr>{cols.map(c=><th key={c} className="table-head">{c.replaceAll('_',' ')}</th>)}{canDelete && endpoint !== '/trips' && <th className="table-head">Action</th>}</tr></thead><tbody>{data.items.map((row,i)=><tr key={String(row[cols[0]])||i} className="border-t hover:bg-slate-50">{cols.map(c=><td key={c} className="table-cell">{typeof row[c]==='number'&&(/cost|amount|premium|damage/.test(c))?money(row[c]):String(row[c]??'—')}</td>)}{canDelete && endpoint !== '/trips' && <td className="table-cell"><button onClick={()=>removeRecord(row[idCol])} className="text-xs font-medium text-red-600 hover:underline">Delete</button></td>}</tr>)}</tbody></table></div>}<div className="border-t px-5 py-3 text-sm text-slate-500">{data?.total||0} total records</div></div>
  </div>
}

export function Insights() { const [data,setData]=useState<any>(); useEffect(()=>{api('/analytics/insights').then(setData)},[]); if(!data)return <div className="panel p-6">Calculating fleet insights…</div>; return <div><p className="text-sm font-medium text-brand">SMART ANALYTICS</p><h1 className="mb-6 text-2xl font-bold">Fleet cost & efficiency signals</h1><div className="grid gap-6 lg:grid-cols-3">{Object.entries(data).map(([key,items]:any)=><section className="panel p-5" key={key}><h2 className="mb-4 capitalize font-semibold">{key.replace('_',' ')}</h2>{items.length?items.map((x:any,i:number)=><div key={i} className="border-t py-3 text-sm"><b>{x.registration_number}</b><div className="text-slate-500">{money(x.total_operating_cost||x.maintenance_cost)} {x.fuel_efficiency_kmpl&&` · ${x.fuel_efficiency_kmpl} km/l`}</div></div>):<p className="text-sm text-slate-500">No signals at this threshold.</p>}</section>)}</div></div> }

