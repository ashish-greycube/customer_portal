<script setup lang="ts">
import AppHeader from '../components/AppHeader.vue'
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Avatar, Badge, Button, Dialog, Password, call, toast } from 'frappe-ui'
import { BASE, errorText, session } from '../data'
import { useSession } from '../lib/session'

const route = useRoute()
const router = useRouter()
const { user, isAdmin } = useSession()

const show = ref(false)
const pw = ref({ current: '', next: '', confirm: '' })
const errors = ref<Record<string, string>>({})
const saving = ref(false)
const CUSTOMER = session.customer
const ACCOUNT_MANAGER = session.accountManager
const CONTACTS = session.contacts

function openPassword() {
  pw.value = { current: '', next: '', confirm: '' }
  errors.value = {}
  show.value = true
}

onMounted(() => {
  if (route.query.password) openPassword()
})
watch(() => route.query.password, (v) => v && openPassword())
watch(show, (v) => !v && route.query.password && router.replace('/account'))

async function save() {
  const e: Record<string, string> = {}
  if (!pw.value.current) e.current = 'Enter your current password'
  if (pw.value.next.length < 8) e.next = 'Use at least 8 characters'
  if (pw.value.confirm !== pw.value.next) e.confirm = 'Passwords do not match'
  errors.value = e
  if (Object.keys(e).length) return
  saving.value = true
  try {
    await call('frappe.core.doctype.user.user.update_password', {
      old_password: pw.value.current,
      new_password: pw.value.next,
      logout_all_sessions: 1,
    })
    show.value = false
    toast.success('Password updated')
    // Changing the password starts a new session, so reload for a fresh CSRF token
    setTimeout(() => (window.location.href = `${BASE}/account`), 800)
  } catch (err) {
    errors.value = { next: errorText(err) }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AppHeader>
    <h1 class="text-2xl text-ink-gray-9">My account</h1>
  </AppHeader>

  <div class="mx-auto max-w-[940px] space-y-6 px-3 pt-5 pb-10 sm:px-5">
    <section class="flex flex-wrap items-center gap-4 rounded-5 border border-outline-gray-1 bg-surface-base p-5">
      <Avatar :label="user.name" size="3xl" />
      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-2">
          <span class="text-xl text-ink-gray-9">{{ user.name }}</span>
          <Badge :label="session.staff ? 'Refteck staff' : isAdmin ? 'Customer main contact' : 'Contact'" :theme="isAdmin ? 'blue' : 'gray'" variant="subtle" />
        </div>
        <div class="mt-1 text-sm text-ink-gray-6">{{ [user.role, user.email].filter(Boolean).join(' · ') }}</div>
        <div class="mt-2 text-p-sm text-ink-gray-5">
          {{ session.staff ? 'Staff view: switch customers from the sidebar to see every record of that customer.' : isAdmin ? 'As customer admin you see every opportunity and document for your company.' : 'You see the opportunities and documents you raised.' }}
        </div>
      </div>
      <Button icon-left="lucide-key-round" label="Change password" @click="openPassword" />
    </section>

    <div class="grid gap-6 md:grid-cols-2">
      <section class="rounded-5 border border-outline-gray-1 bg-surface-base p-5">
        <h2 class="text-lg-semibold text-ink-gray-8">Company</h2>
        <dl class="mt-4 space-y-3 text-sm">
          <div class="flex gap-4"><dt class="w-24 shrink-0 text-ink-gray-5">Customer</dt><dd class="text-ink-gray-8">{{ CUSTOMER.name }}</dd></div>
          <div class="flex gap-4"><dt class="w-24 shrink-0 text-ink-gray-5">Customer ID</dt><dd class="text-ink-gray-8 tabular-nums">{{ CUSTOMER.id }}</dd></div>
          <div class="flex gap-4"><dt class="w-24 shrink-0 text-ink-gray-5">Address</dt><dd class="text-p-sm text-ink-gray-8">{{ CUSTOMER.address }}</dd></div>
        </dl>
      </section>

      <section class="rounded-5 border border-outline-gray-1 bg-surface-base p-5">
        <h2 class="text-lg-semibold text-ink-gray-8">Refteck primary account manager</h2>
        <p v-if="!ACCOUNT_MANAGER" class="mt-4 text-p-sm text-ink-gray-5">
          No account manager assigned yet. Write to <a href="mailto:abc@refteck.in" class="font-semibold text-[var(--rt-link)]">abc@refteck.in</a>.
        </p>
        <template v-else>
        <div class="mt-4 flex items-center gap-3">
          <Avatar :label="ACCOUNT_MANAGER.name" size="2xl" />
          <div>
            <div class="text-base text-ink-gray-9">{{ ACCOUNT_MANAGER.name }}</div>
            <div class="text-sm text-ink-gray-5">{{ [ACCOUNT_MANAGER.title, ACCOUNT_MANAGER.location].filter(Boolean).join(' · ') }}</div>
          </div>
        </div>
        <div class="mt-4 space-y-2 text-sm text-ink-gray-7">
          <div class="flex items-center gap-2"><span class="lucide-mail size-4 text-ink-gray-5" aria-hidden="true" />{{ ACCOUNT_MANAGER.email }}</div>
          <div v-if="ACCOUNT_MANAGER.phone" class="flex items-center gap-2"><span class="lucide-phone size-4 text-ink-gray-5" aria-hidden="true" />{{ ACCOUNT_MANAGER.phone }}</div>
        </div>
        </template>
      </section>
    </div>

    <section class="rounded-5 border border-outline-gray-1 bg-surface-base">
      <header class="px-5 pt-5">
        <h2 class="text-lg-semibold text-ink-gray-8">Company contacts</h2>
        <p class="mt-1 text-p-sm text-ink-gray-5">The main contact is the customer admin and sees all records. Other contacts see what they raised.</p>
      </header>
      <div class="mt-3 divide-y divide-outline-gray-1 px-5 pb-2">
        <div v-for="c in CONTACTS" :key="c.id" class="flex items-center gap-3 py-3">
          <Avatar :label="c.name" size="lg" />
          <div class="min-w-0 flex-1">
            <div class="truncate text-base text-ink-gray-8">{{ c.name }}</div>
            <div class="truncate text-sm text-ink-gray-5">{{ [c.role, c.email].filter(Boolean).join(' · ') }}</div>
          </div>
          <Badge v-if="c.isMainContact" label="Main contact" theme="blue" variant="subtle" />
        </div>
      </div>
    </section>
  </div>

  <Dialog v-model:open="show" title="Change password">
    <div class="space-y-4">
      <Password v-model="pw.current" label="Current password" required :error="errors.current" />
      <Password v-model="pw.next" label="New password" description="At least 8 characters." required :error="errors.next" />
      <Password v-model="pw.confirm" label="Confirm new password" required :error="errors.confirm" />
      <div class="flex justify-end gap-2 pt-2">
        <Button label="Cancel" @click="show = false" />
        <Button variant="solid" theme="gray" class="rt-primary" label="Update password" :loading="saving" @click="save" />
      </div>
    </div>
  </Dialog>
</template>
