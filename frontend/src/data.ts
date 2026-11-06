import { reactive } from 'vue'
import { call } from 'frappe-ui'

export const BASE = '/customer-portal'

export const STEPS = [
  'Opportunity raised',
  'Quotation',
  'PO upload',
  'PO confirmation',
  'Ready for dispatch',
  'Dispatched',
]

// Whitelisted methods in customer_portal/api.py
export const api = <T = any>(method: string, args: Record<string, any> = {}) =>
  call<T>(`customer_portal.api.${method}`, args)

export const errorText = (e: any) =>
  (e?.messages?.length ? e.messages.join(' ') : e?.message || 'Something went wrong').replace(/<[^>]+>/g, '')

export const session = reactive<{
  user: any
  staff: boolean
  customer: any
  accountManager: any
  contacts: any[]
  company: { name: string; line: string }
  unread: number
}>({
  user: null,
  staff: false,
  customer: null,
  accountManager: null,
  contacts: [],
  company: { name: 'Refteck', line: '' },
  unread: 0,
})

export async function loadSession() {
  try {
    Object.assign(session, await api('get_session'))
  } catch {
    session.user = null
  }
}

export const contactName = (id: string) => session.contacts.find((c) => c.id === id)?.name ?? ''

export async function refreshUnread() {
  try {
    session.unread = await api('get_unread')
  } catch {
    // keep the last count
  }
}
