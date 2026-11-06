import { computed } from 'vue'
import { session } from '../data'

// Customer admin (the customer's primary contact) sees every record of the customer.
// Other contacts see what they raised. The server applies the same rule.
export function useSession() {
  const user = computed(() => session.user)
  const isAdmin = computed(() => !!session.user?.isMainContact)
  return { user, isAdmin }
}
