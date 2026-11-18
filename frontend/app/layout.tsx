import './globals.css'
import type { ReactNode } from 'react'

export const metadata = { title: 'Smart Fleet Management', description: 'Fleet management and analytics dashboard' }

export default function RootLayout({ children }: { children: ReactNode }) {
  return <html lang="en"><body>{children}</body></html>
}
