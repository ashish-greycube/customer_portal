import { session } from '../data'

export const uniq = (xs: any[]) => [...new Set(xs.filter(Boolean))].sort()
export const opts = (values: string[], all: string) => [{ label: all, value: '' }, ...values.map((v) => ({ label: v, value: v }))]
export const ownerOpts = () => [{ label: 'Anyone', value: '' }, ...session.contacts.map((c) => ({ label: c.name, value: c.id }))]

export function inRange(date: string, range: any) {
  if (!Array.isArray(range) || !range[0] || !range[1]) return true
  const d = String(date).slice(0, 10)
  return d >= String(range[0]).slice(0, 10) && d <= String(range[1]).slice(0, 10)
}

export const matches = (text: string, q: string) => !q.trim() || text.toLowerCase().includes(q.trim().toLowerCase())
