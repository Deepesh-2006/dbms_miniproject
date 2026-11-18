'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { ReactNode, useEffect, useState } from 'react'
import { nav } from './screens'
import { token } from '@/lib/api'

const hrefFor = (item: string) => `/${item.toLowerCase()}`

export default function Shell({ children }: { children: ReactNode }) {
  const router = useRouter()
  const path = usePathname()
  const [ready, setReady] = useState(false)
  useEffect(() => { if (!token()) router.replace('/login'); else setReady(true) }, [router])
  if (!ready) return <div className="p-8 text-slate-500">Loading…</div>
  return <div className="min-h-screen lg:flex">
    <aside className="bg-navy px-4 py-5 text-slate-300 lg:fixed lg:inset-y-0 lg:w-64">
      <div className="mb-8 px-3"><p className="text-xs font-bold tracking-[.2em] text-brand">SMART FLEET</p><p className="mt-1 text-lg font-semibold text-white">Fleet Command</p></div>
      <nav className="flex gap-1 overflow-x-auto lg:block">
        {nav.map(item => <Link key={item} href={hrefFor(item)} className={`block whitespace-nowrap rounded-lg px-3 py-2.5 text-left text-sm lg:mb-1 ${path === hrefFor(item) ? 'bg-white/10 text-white' : 'hover:bg-white/5'}`}>{item}</Link>)}
      </nav>
      <button onClick={() => { localStorage.clear(); router.replace('/login') }} className="mt-8 px-3 text-sm text-slate-400 hover:text-white">Sign out</button>
    </aside>
    <main className="min-w-0 flex-1 p-5 lg:ml-64 lg:p-8">{children}</main>
  </div>
}
