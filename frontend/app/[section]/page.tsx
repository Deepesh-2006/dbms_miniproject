import { notFound } from 'next/navigation'
import Shell from '@/components/Shell'
import { TablePage } from '@/components/screens'

const pageEndpoint: Record<string, string> = {
  Vehicles: '/vehicles',
  Drivers: '/drivers',
  Trips: '/trips',
  Fuel: '/fuel',
  Maintenance: '/maintenance',
  Accidents: '/accidents',
  Insurance: '/insurance',
  Expenses: '/expenses',
}
const titles = Object.keys(pageEndpoint)

export function generateStaticParams() { return titles.map(t => ({ section: t.toLowerCase() })) }

export default async function Page({ params }: { params: Promise<{ section: string }> }) {
  const { section } = await params
  const title = titles.find(t => t.toLowerCase() === section)
  if (!title) notFound()
  return <Shell><TablePage title={title} endpoint={pageEndpoint[title]} /></Shell>
}
