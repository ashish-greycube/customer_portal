<script setup lang="ts">
import { Button, call } from 'frappe-ui'
import { BASE, session } from '../data'

async function logout() {
  await call('logout').catch(() => {})
  window.location.href = `${BASE}/login`
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-[var(--rt-backdrop)] px-4">
    <div class="w-full max-w-sm text-center">
      <div class="text-3xl font-bold tracking-[.06em] text-[var(--rt-accent)]">REFTECK</div>
      <div class="rt-tricolor mx-auto mt-2 h-[3px] w-12 rounded-full" />
      <div class="mt-6 space-y-3 overflow-hidden rounded-6 border border-outline-gray-1 border-t-4 border-t-[var(--rt-navy)] bg-surface-base p-6 shadow-sm">
        <span class="lucide-lock mx-auto block size-6 text-ink-gray-5" aria-hidden="true" />
        <h1 class="text-xl text-ink-gray-9">No customer account linked</h1>
        <p class="text-p-sm text-ink-gray-6">
          You are signed in as {{ session.user?.email }}, but this login is not linked to a Refteck customer yet.
        </p>
        <Button label="Sign out" icon-left="lucide-log-out" class="w-full" @click="logout" />
      </div>
      <p class="mt-6 text-p-xs text-ink-gray-5">Need access? Ask <a href="mailto:abc@refteck.in" class="font-semibold text-[var(--rt-link)]">abc@refteck.in</a></p>
    </div>
  </div>
</template>
