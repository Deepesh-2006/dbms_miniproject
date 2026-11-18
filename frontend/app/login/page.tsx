'use client'
import { useRouter } from 'next/navigation'
import { Login } from '@/components/screens'

export default function LoginPage() {
  const router = useRouter()
  return <Login onSuccess={() => router.replace('/dashboard')} />
}
