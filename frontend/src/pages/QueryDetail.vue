<script setup lang="ts">
import AppHeader from '../components/AppHeader.vue'
import { ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { Avatar, Badge, Breadcrumbs, Button, FormControl, Skeleton, toast } from 'frappe-ui'
import dayjs from 'dayjs'
import EmptyState from '../components/EmptyState.vue'
import { api, contactName, errorText, session } from '../data'
import { fmtDate, themeFor } from '../lib/format'

const props = defineProps<{ name: string }>()

const query = ref<any>(null)
const loading = ref(true)
const busy = ref(false)

async function load() {
  try {
    query.value = await api('get_query', { name: props.name })
  } catch {
    query.value = null
  } finally {
    loading.value = false
  }
}
watch(() => props.name, () => ((loading.value = true), load()), { immediate: true })

const reply = ref('')
const handler = () => session.accountManager?.name || 'Refteck'
const author = (m: any) => (m.by === 'refteck' ? m.author || handler() : contactName(m.by) || m.by)

async function send() {
  if (!reply.value.trim() || !query.value) return
  busy.value = true
  try {
    await api('reply_query', { name: props.name, text: reply.value.trim() })
    reply.value = ''
    toast.success('Reply sent to Refteck')
    await load()
  } catch (e) {
    toast.error(errorText(e))
  } finally {
    busy.value = false
  }
}

async function toggleResolved() {
  if (!query.value) return
  const resolved = query.value.status === 'Resolved'
  busy.value = true
  try {
    await api('set_query_resolved', { name: props.name, resolved: resolved ? 0 : 1 })
    toast.success(resolved ? 'Query reopened' : 'Query marked as resolved')
    await load()
  } catch (e) {
    toast.error(errorText(e))
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <AppHeader>
    <Breadcrumbs :items="[{ label: 'Queries & issues', route: { path: '/queries' } }, { label: name }]" />
    <Button
      v-if="query && !session.staff"
      class="ml-auto"
      :icon-left="query.status === 'Resolved' ? 'lucide-rotate-ccw' : 'lucide-circle-check'"
      :label="query.status === 'Resolved' ? 'Reopen' : 'Mark resolved'"
      :loading="busy"
      @click="toggleResolved"
    />
  </AppHeader>

  <div v-if="loading" class="space-y-3 px-3 pt-5 sm:px-5">
    <Skeleton class="h-8 w-80 rounded-4" />
    <Skeleton v-for="i in 3" :key="i" class="h-16 w-full rounded-4" />
  </div>
  <EmptyState v-else-if="!query" title="Query not available" text="It does not exist or was raised by another contact." icon="lucide-lock" />

  <div v-else class="flex flex-col lg:flex-row">
    <div class="min-w-0 flex-1 px-3 pt-5 pb-10 sm:px-5">
      <div class="flex flex-wrap items-center gap-3">
        <h1 class="text-2xl text-ink-gray-9">{{ query.subject }}</h1>
        <Badge :label="query.status" :theme="themeFor(query.status)" variant="subtle" />
      </div>

      <div class="mt-6 space-y-5">
        <div v-for="(m, i) in query.messages" :key="i" class="flex gap-3">
          <Avatar :label="author(m)" size="lg" />
          <div class="min-w-0 flex-1">
            <div class="flex items-baseline gap-2">
              <span class="text-base-semibold text-ink-gray-8">{{ author(m) }}</span>
              <span v-if="m.by === 'refteck'" class="text-xs text-ink-gray-5">Refteck</span>
              <span class="text-xs text-ink-gray-5">{{ dayjs(m.at).format('DD MMM, HH:mm') }}</span>
            </div>
            <p class="mt-1 whitespace-pre-line text-p-base text-ink-gray-7">{{ m.text }}</p>
          </div>
        </div>
      </div>

      <div v-if="!session.staff" class="mt-8 space-y-2 border-t border-outline-gray-1 pt-5">
        <FormControl v-model="reply" type="textarea" label="Reply" :rows="3" />
        <div class="flex justify-end">
          <Button variant="solid" theme="gray" class="rt-primary" icon-left="lucide-send" label="Send reply" :disabled="!reply.trim()" :loading="busy" @click="send" />
        </div>
      </div>
    </div>

    <aside class="shrink-0 border-outline-gray-1 px-3 pt-5 pb-10 sm:px-5 lg:w-[20rem] lg:border-l">
      <dl class="space-y-4 text-sm">
        <div><dt class="text-ink-gray-5">ID</dt><dd class="mt-1 text-ink-gray-8 tabular-nums">{{ query.name }}</dd></div>
        <div><dt class="text-ink-gray-5">Category</dt><dd class="mt-1 text-ink-gray-8">{{ query.category }}</dd></div>
        <div>
          <dt class="text-ink-gray-5">Related document</dt>
          <dd class="mt-1">
            <RouterLink v-if="query.related" :to="`/print/${query.related.doctype}/${query.related.name}`" class="font-semibold text-[var(--rt-link)]">
              {{ query.related.name }}
            </RouterLink>
            <span v-else class="text-ink-gray-5">None</span>
          </dd>
        </div>
        <div><dt class="text-ink-gray-5">Raised by</dt><dd class="mt-1 text-ink-gray-8">{{ query.ownerName }}</dd></div>
        <div><dt class="text-ink-gray-5">Raised on</dt><dd class="mt-1 text-ink-gray-8">{{ fmtDate(query.date) }}</dd></div>
        <div><dt class="text-ink-gray-5">Handled by</dt><dd class="mt-1 text-ink-gray-8">{{ handler() }}</dd></div>
      </dl>
    </aside>
  </div>
</template>
