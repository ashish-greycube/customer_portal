<script setup lang="ts">
import { useRouter } from 'vue-router'
import { Avatar, Button, Dropdown, call } from 'frappe-ui'
import { BASE, session } from '../data'
import { useSession } from '../lib/session'

const router = useRouter()
const { user, isAdmin } = useSession()

const options = [
  { label: 'My account', icon: 'lucide-user', onClick: () => router.push('/account') },
  { label: 'Change password', icon: 'lucide-key-round', onClick: () => router.push('/account?password=1') },
  { label: 'Log out', icon: 'lucide-log-out', onClick: logout },
]

async function logout() {
  await call('logout').catch(() => {})
  window.location.href = `${BASE}/login`
}
</script>

<template>
  <Dropdown :options="options">
    <Button variant="ghost" class="!h-auto py-1 pl-1 pr-2" :aria-label="`Account menu for ${user.name}`">
      <div class="flex items-center gap-2 text-left">
        <Avatar :label="user.name" size="md" />
        <div class="hidden min-w-0 sm:block">
          <div class="truncate text-sm leading-tight text-ink-gray-8">{{ user.name }}</div>
          <div class="truncate text-xs leading-tight text-ink-gray-5">{{ session.staff ? 'Refteck staff' : isAdmin ? 'Customer admin' : 'Contact' }}</div>
        </div>
        <span class="lucide-chevron-down size-4 text-ink-gray-5" aria-hidden="true" />
      </div>
    </Button>
  </Dropdown>
</template>
