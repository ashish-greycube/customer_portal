<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import { DesktopShell, FrappeUIProvider, ScrollArea, Sidebar, SidebarItem } from 'frappe-ui'
import { session } from './data'
import CustomerSwitcher from './components/CustomerSwitcher.vue'

const route = useRoute()

const bare = computed(() => route.meta?.bare)
const unread = computed(() => session.unread)

const nav = [
  { label: 'Dashboard', icon: 'lucide-layout-dashboard', route: '/' },
  { group: 'Sales documents' },
  { label: 'Opportunities', icon: 'lucide-target', route: '/opportunities' },
  { label: 'Quotations', icon: 'lucide-file-text', route: '/quotations' },
  { label: 'PO submission', icon: 'lucide-file-up', route: '/po-submission' },
  { label: 'Sales orders', icon: 'lucide-shopping-cart', route: '/sales-orders' },
  { label: 'Shipping', icon: 'lucide-truck', route: '/sales-invoices' },
  { group: 'Support' },
  { label: 'Queries & issues', icon: 'lucide-message-circle-question', route: '/queries' },
  { label: 'Notifications', icon: 'lucide-bell', route: '/notifications', count: true },
]
</script>

<template>
  <FrappeUIProvider>
  <div class="h-screen w-full bg-surface-base text-ink-gray-9">
    <RouterView v-if="bare" />
    <DesktopShell v-else>
      <template #sidebar>
        <Sidebar width="14rem" class="rt-nav border-r">
          <div class="relative px-4 pt-4 pb-3.5">
            <div class="text-lg-semibold text-[var(--rt-accent)]">Customer Portal</div>
            <div class="mt-1 text-xs text-ink-gray-5">
              by <b class="font-bold tracking-[.06em] text-[var(--rt-orange)]">REFTECK</b>
            </div>
            <div class="rt-tricolor absolute inset-x-4 bottom-0 h-[3px] rounded-full" />
          </div>
          <CustomerSwitcher v-if="session.staff" />
          <ScrollArea class="min-h-0 flex-1" viewport-class="px-2 pt-2 pb-4">
            <div class="space-y-0.5">
              <template v-for="item in nav" :key="item.label || item.group">
                <p v-if="item.group" class="px-2 pt-4 pb-1 text-xs text-ink-gray-5">{{ item.group }}</p>
                <SidebarItem v-else :label="item.label" :icon="item.icon" :route="item.route">
                  <template v-if="item.count && unread" #suffix>
                    <span class="rounded-full bg-[var(--rt-orange)] px-1.5 text-2xs font-semibold leading-4 text-[#fff] tabular-nums">{{ unread }}</span>
                  </template>
                </SidebarItem>
              </template>
            </div>
          </ScrollArea>
        </Sidebar>
      </template>
      <div class="h-full overflow-y-auto">
        <RouterView />
      </div>
    </DesktopShell>
  </div>
  </FrappeUIProvider>
</template>

<style>
/* Refteck brand tokens, from the Tail Spend Hub reference */
:root {
  --rt-navy: #182a4f;
  --rt-navy-hover: #22386a;
  --rt-navy-soft: #e9edf5;
  --rt-accent: #182a4f;
  --rt-orange: #ed7923;
  --rt-orange-soft: #fdf1e6;
  --rt-orange-ink: #b4570f;
  --rt-green: #268c42;
  --rt-link: #284a8c;
  --rt-backdrop: #e3e7ee;
}
[data-theme='dark'] {
  --rt-navy: #26407a;
  --rt-navy-hover: #3a5288;
  --rt-navy-soft: #1d2b49;
  --rt-accent: #8fb0ea;
  --rt-orange: #f28c3f;
  --rt-orange-soft: #3a2414;
  --rt-orange-ink: #f6a868;
  --rt-green: #4cb06a;
  --rt-link: #8fb0ea;
  --rt-backdrop: #0c1424;
}
.rt-primary {
  background: var(--rt-navy) !important;
  border-color: var(--rt-navy) !important;
  color: #fff !important;
}
.rt-primary:hover {
  background: var(--rt-navy-hover) !important;
}
.rt-nav a.router-link-exact-active,
.rt-nav [aria-current='page'] {
  background: var(--rt-navy-soft) !important;
  color: var(--rt-accent) !important;
  box-shadow: inset 3px 0 0 var(--rt-orange) !important;
  font-weight: 600;
}
.rt-highlight {
  background: var(--rt-orange) !important;
  border-color: var(--rt-orange) !important;
  color: #fff !important;
  box-shadow: 0 0 0 3px var(--rt-orange-soft) !important;
}
.rt-highlight:hover {
  filter: brightness(0.94);
}
.rt-tricolor {
  background: linear-gradient(90deg, #ed7923 0 33.33%, #268c42 33.33% 66.66%, var(--rt-navy) 66.66%);
}
</style>
