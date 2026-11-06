<script setup lang="ts">
import AppHeader from '../components/AppHeader.vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Skeleton, toast } from 'frappe-ui'
import FilterBar from '../components/FilterBar.vue'
import { inRange } from '../lib/filters'
import dayjs from 'dayjs'
import EmptyState from '../components/EmptyState.vue'
import { api, errorText, session } from '../data'

const router = useRouter()
const items = ref<any[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    items.value = await api('get_notifications')
  } catch (e) {
    toast.error(errorText(e))
  } finally {
    loading.value = false
  }
})

const f = reactive<Record<string, any>>({ read: '', range: [] })
const filterDefs = [
  { key: 'read', label: 'Show', options: [{ label: 'All', value: '' }, { label: 'Unread', value: 'unread' }, { label: 'Read', value: 'read' }] },
  { key: 'range', label: 'Received between', type: 'daterange' },
]
const all = computed(() => [...items.value].sort((a, b) => b.at.localeCompare(a.at)))
const unread = computed(() => all.value.filter((n) => !n.read).length)
const list = computed(() =>
  all.value.filter((n) => (!f.read || (f.read === 'unread') === !n.read) && inRange(n.at, f.range)),
)

async function markRead(names?: string[]) {
  try {
    session.unread = await api('mark_notifications_read', { names })
  } catch (e) {
    toast.error(errorText(e))
  }
}
function openItem(n: any) {
  if (!n.read) {
    n.read = true
    markRead([n.id])
  }
  router.push(n.to)
}
function markAll() {
  all.value.forEach((n) => (n.read = true))
  markRead()
}
</script>

<template>
  <AppHeader>
    <h1 class="text-2xl text-ink-gray-9">Notifications</h1>
    <Button class="ml-auto" icon-left="lucide-check-check" label="Mark all as read" :disabled="!unread" @click="markAll" />
  </AppHeader>

  <div class="mx-auto max-w-[940px] px-3 pt-5 pb-10 sm:px-5">
    <FilterBar :filters="filterDefs" :model="f" :shown="list.length" :total="all.length" />
    <div v-if="loading" class="mt-4 space-y-2">
      <Skeleton v-for="i in 5" :key="i" class="h-12 w-full rounded-4" />
    </div>
    <div v-else-if="list.length" class="mt-4 divide-y divide-outline-gray-1">
      <button
        v-for="n in list"
        :key="n.id"
        type="button"
        class="flex w-full items-start gap-3 rounded-4 px-2 py-3 text-left hover:bg-surface-gray-1"
        @click="openItem(n)"
      >
        <span class="mt-2 size-2 shrink-0 rounded-full" :class="n.read ? 'bg-transparent' : 'bg-[var(--rt-orange)]'" aria-hidden="true" />
        <span :class="[n.icon, 'mt-0.5 size-4 shrink-0 text-[var(--rt-accent)]']" aria-hidden="true" />
        <div class="min-w-0 flex-1">
          <div class="truncate text-base" :class="n.read ? 'text-ink-gray-7' : 'text-ink-gray-9 font-medium'">{{ n.title }}</div>
          <div class="mt-0.5 text-p-sm text-ink-gray-5">{{ n.body }}</div>
        </div>
        <span class="shrink-0 text-xs text-ink-gray-5">{{ dayjs(n.at).fromNow() }}</span>
      </button>
    </div>
    <EmptyState
      v-else
      :title="session.staff ? 'No notifications in staff view' : 'No notifications match these filters'"
      :text="session.staff ? 'Customers see their notifications when they sign in.' : 'New updates from Refteck will appear here.'"
      icon="lucide-bell"
    />
  </div>
</template>
