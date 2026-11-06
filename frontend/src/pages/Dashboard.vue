<script setup lang="ts">
import AppHeader from '../components/AppHeader.vue'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Avatar, Button, Skeleton, toast } from 'frappe-ui'
import { STEPS, api, errorText, session } from '../data'
import { useSession } from '../lib/session'

const { user, isAdmin } = useSession()
const CUSTOMER = session.customer
const ACCOUNT_MANAGER = session.accountManager

const data = ref<any>(null)
onMounted(async () => {
  try {
    data.value = await api('get_dashboard')
    session.unread = data.value.counts.unread
  } catch (e) {
    toast.error(errorText(e))
  }
})

const groups = computed(() => {
  const c = data.value?.counts ?? {}
  return [
    {
      title: 'Opportunities, quotations & POs',
      cards: [
        { label: 'Open opportunities', value: c.openOpportunities, sub: 'Awaiting a quotation from Refteck', icon: 'lucide-target', to: '/opportunities?status=Open' },
        { label: 'Quotations awaiting PO', value: c.openQuotations, sub: 'Ready for your purchase order', icon: 'lucide-file-text', to: '/quotations?status=Open', action: true },
        { label: 'POs pending confirmation', value: c.pendingPOs, sub: 'Being checked by Refteck', icon: 'lucide-file-up', to: '/po-submission' },
      ],
    },
    {
      title: 'Orders & shipping',
      cards: [
        { label: 'Orders in processing', value: c.processingOrders, sub: 'Confirmed, not yet packed', icon: 'lucide-shopping-cart', to: '/sales-orders?status=Processing' },
        { label: 'Ready for dispatch', value: c.readyForDispatch, sub: 'Draft sales invoices', icon: 'lucide-package-check', to: '/sales-invoices?status=Ready%20for%20dispatch' },
        { label: 'Dispatched', value: c.dispatched, sub: 'Submitted sales invoices', icon: 'lucide-truck', to: '/sales-invoices?status=Dispatched' },
      ],
    },
    {
      title: 'Support',
      cards: [
        { label: 'Open queries', value: c.openQueries, sub: `${c.queriesAwaitingYou ?? 0} awaiting your reply`, icon: 'lucide-message-circle-question', to: '/queries', action: c.queriesAwaitingYou > 0 },
        { label: 'Unread notifications', value: c.unread, sub: 'Updates from Refteck', icon: 'lucide-bell', to: '/notifications', action: true },
      ],
    },
  ]
})

const pipeline = computed(() => STEPS.map((label, i) => ({ label, n: i + 1, count: data.value?.pipeline?.[i] ?? 0 })))
</script>

<template>
  <AppHeader>
    <h1 class="text-2xl text-ink-gray-9">Dashboard</h1>
  </AppHeader>

  <div class="mx-auto max-w-5xl space-y-6 px-3 pt-5 pb-10 sm:px-5">
    <div class="flex flex-col gap-4 lg:flex-row lg:items-stretch">
      <div class="flex-1 self-center">
        <p class="relative inline-block pb-2 text-xl text-[var(--rt-accent)]">
          Welcome back, {{ user.name.split(' ')[0] }}
          <span class="rt-tricolor absolute bottom-0 left-0 h-[3px] w-[42px] rounded-full" />
        </p>
        <p class="mt-2 text-p-sm text-ink-gray-5">
          {{ CUSTOMER.name }} ·
          {{ session.staff ? 'Refteck staff view, showing all records of this customer' : isAdmin ? 'Customer admin, showing all records for your company' : 'Showing the records you raised' }}
        </p>
      </div>

      <section class="flex flex-wrap items-center gap-4 rounded-5 border border-outline-gray-1 border-l-4 border-l-[var(--rt-navy)] bg-surface-base px-4 py-3 lg:w-[30rem]">
        <Avatar :label="ACCOUNT_MANAGER?.name || 'Refteck'" size="2xl" />
        <div class="min-w-0 flex-1">
          <div class="text-xs text-ink-gray-5">Your account manager</div>
          <div class="truncate text-base font-semibold text-[var(--rt-accent)]">{{ ACCOUNT_MANAGER?.name || 'Refteck sales team' }}</div>
          <div class="truncate text-xs text-ink-gray-6">{{ ACCOUNT_MANAGER ? [ACCOUNT_MANAGER.email, ACCOUNT_MANAGER.phone].filter(Boolean).join(' · ') : 'abc@refteck.in' }}</div>
        </div>
        <div class="flex gap-2">
          <Button icon="lucide-mail" :href="`mailto:${ACCOUNT_MANAGER?.email || 'abc@refteck.in'}`" aria-label="Email account manager" />
          <Button v-if="!session.staff" label="Raise a query" icon-left="lucide-plus" route="/queries?new=1" />
        </div>
      </section>
    </div>

    <section v-for="g in groups" :key="g.title" class="space-y-3">
      <h2 class="text-sm text-ink-gray-5">{{ g.title }}</h2>
      <div class="grid grid-cols-2 gap-3 lg:grid-cols-3">
        <RouterLink
          v-for="c in g.cards"
          :key="c.label"
          :to="c.to"
          class="rounded-5 border border-outline-gray-1 bg-surface-base p-4 transition hover:-translate-y-px hover:border-[var(--rt-link)]"
          :class="c.action && c.value ? 'border-l-4 border-l-[var(--rt-orange)]' : ''"
        >
          <div class="flex items-center justify-between gap-2">
            <span class="truncate text-sm font-semibold text-ink-gray-7">{{ c.label }}</span>
            <span :class="[c.icon, 'size-4 shrink-0 text-[var(--rt-accent)] opacity-70']" aria-hidden="true" />
          </div>
          <Skeleton v-if="!data" class="mt-2 h-9 w-12 rounded-4" />
          <div v-else class="mt-2 text-3xl font-bold text-[var(--rt-accent)] tabular-nums">{{ c.value }}</div>
          <div class="mt-1 truncate text-xs text-ink-gray-5">{{ c.sub }}</div>
        </RouterLink>
      </div>
    </section>

    <section class="rounded-5 border border-outline-gray-1 bg-surface-base">
      <header class="flex items-center justify-between px-4 pt-4">
        <h2 class="text-lg-semibold text-ink-gray-8">Opportunities by workflow step</h2>
        <Button variant="ghost" size="sm" label="View all" route="/opportunities" />
      </header>
      <div class="grid grid-cols-3 divide-outline-gray-2 p-4 sm:grid-cols-6 sm:divide-x">
        <div v-for="p in pipeline" :key="p.label" class="px-3 py-2">
          <div class="flex items-center gap-1.5 text-xs text-ink-gray-5 tabular-nums">
            <span class="size-2 rounded-full" :class="p.n === 6 ? 'bg-[var(--rt-green)]' : p.n >= 5 ? 'bg-[var(--rt-orange)]' : 'bg-[var(--rt-navy)]'" />
            Step {{ p.n }}
          </div>
          <div class="mt-1 text-2xl font-bold text-[var(--rt-accent)] tabular-nums">{{ p.count }}</div>
          <div class="mt-0.5 text-xs text-ink-gray-6">{{ p.label }}</div>
        </div>
      </div>
    </section>
  </div>
</template>
