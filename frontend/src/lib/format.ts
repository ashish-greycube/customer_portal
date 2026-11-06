import dayjs from 'dayjs'

const formatters: Record<string, Intl.NumberFormat> = {}

export function fmtMoney(n: number, currency?: string) {
  const code = currency || 'USD'
  try {
    formatters[code] ??= new Intl.NumberFormat('en-US', { style: 'currency', currency: code })
    return formatters[code].format(n || 0)
  } catch {
    return `${code} ${fmtQty(n || 0)}`
  }
}
export const fmtDate = (s: string) => (s ? dayjs(s).format('DD MMM YYYY') : '—')
export const fmtQty = (n: number) => new Intl.NumberFormat('en-US').format(n)

const THEMES: Record<string, string> = {
  Open: 'blue',
  Quotation: 'amber',
  Converted: 'green',
  'PO submitted': 'violet',
  Ordered: 'green',
  Expired: 'gray',
  Lost: 'red',
  Closed: 'gray',
  'Pending confirmation': 'amber',
  Confirmed: 'green',
  Returned: 'red',
  Processing: 'blue',
  'Ready for dispatch': 'amber',
  Dispatched: 'green',
  'Awaiting Refteck': 'blue',
  'Awaiting you': 'amber',
  Resolved: 'green',
}

export const themeFor = (s: string) => THEMES[s] ?? 'gray'
