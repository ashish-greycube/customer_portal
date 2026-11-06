<script setup lang="ts">
import AppHeader from '../components/AppHeader.vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Badge, Button, Dialog, FormControl, Skeleton, toast } from 'frappe-ui'
import FilterBar from '../components/FilterBar.vue'
import { inRange, matches, opts, ownerOpts } from '../lib/filters'
import { List, ListHeader, ListHeaderCell, ListRows, ListRow, ListCell } from 'frappe-ui/list'
import dayjs from 'dayjs'
import EmptyState from '../components/EmptyState.vue'
import { api, errorText, session } from '../data'
import { themeFor } from '../lib/format'
import { useSession } from '../lib/session'

const route = useRoute()
const router = useRouter()
const { isAdmin } = useSession()

const queries = ref<any[]>([])
const loading = ref(true)
const docs = ref<Record<string, any[]>>({})
const all = computed(() => queries.value)
const CATEGORIES = ['Delivery', 'Documents', 'Quantity or quality', 'Commercial', 'Other']
const f = reactive<Record<string, any>>({ q: '', status: '', category: '', owner: '', range: [] })
const filterDefs = computed(() => [
  { key: 'q', label: 'Search', type: 'search', placeholder: 'ID, subject or document' },
  { key: 'status', label: 'Status', options: [{ label: 'All statuses', value: '' }, { label: 'Open (not resolved)', value: 'open' }, ...opts(['Awaiting Refteck', 'Awaiting you', 'Resolved'], '').slice(1)] },
  { key: 'category', label: 'Category', options: opts(CATEGORIES, 'All categories') },
  ...(isAdmin.value ? [{ key: 'owner', label: 'Raised by', options: ownerOpts() }] : []),
  { key: 'range', label: 'Raised between', type: 'daterange' },
])
const filtered = computed(() =>
  all.value
    .filter(
      (q) =>
        matches(`${q.name} ${q.subject} ${q.related?.name ?? ''}`, f.q) &&
        (!f.status || (f.status === 'open' ? q.status !== 'Resolved' : q.status === f.status)) &&
        (!f.category || q.category === f.category) &&
        (!f.owner || q.owner === f.owner) &&
        inRange(q.date, f.range),
    )
    .sort((a, b) => b.updated.localeCompare(a.updated)),
)

const show = ref(false)
const blank = () => ({ subject: '', category: 'Delivery', related: '', text: '' })
const form = ref(blank())
const errors = ref<Record<string, string>>({})

const RELATED_TYPES = ['sales-invoice', 'sales-order', 'po-submission', 'quotation', 'opportunity']
const relatedOptions = computed(() => {
  const options = [
    { label: 'None', value: '' },
    ...RELATED_TYPES.flatMap((dt) =>
      (docs.value[dt] ?? []).map((r) => ({ label: `${r.name} · ${r.title}`, value: `${dt}|${r.name}` })),
    ),
  ]
  // Keep a preselected document even if it is older than the loaded lists
  const pre = form.value.related
  if (pre && !options.some((o) => o.value === pre)) options.push({ label: pre.split('|')[1], value: pre })
  return options
})

async function loadDocs() {
  if (Object.keys(docs.value).length) return
  const lists = await Promise.all(RELATED_TYPES.map((doctype) => api('get_records', { doctype }).catch(() => [])))
  docs.value = Object.fromEntries(RELATED_TYPES.map((dt, i) => [dt, lists[i].slice(0, 100)]))
}

function openNew(related = '') {
  form.value = { ...blank(), related }
  errors.value = {}
  show.value = true
  loadDocs()
}

onMounted(async () => {
  if (route.query.new && !session.staff) openNew((route.query.related as string) || '')
  try {
    queries.value = await api('get_queries')
  } catch (e) {
    toast.error(errorText(e))
  } finally {
    loading.value = false
  }
})

const creating = ref(false)
async function create() {
  const e: Record<string, string> = {}
  if (!form.value.subject.trim()) e.subject = 'Add a subject'
  if (!form.value.text.trim()) e.text = 'Describe the query or issue'
  errors.value = e
  if (Object.keys(e).length) return
  creating.value = true
  try {
    const id = await api('create_query', { ...form.value })
    show.value = false
    toast.success(`${id} raised`)
    router.push(`/queries/${id}`)
  } catch (err) {
    toast.error(errorText(err))
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <AppHeader>
    <h1 class="text-2xl text-ink-gray-9">Queries &amp; issues</h1>
    <Button v-if="!session.staff" variant="solid" theme="gray" icon-left="lucide-plus" label="Raise a query" class="rt-primary ml-auto" @click="openNew()" />
  </AppHeader>

  <div class="px-3 pt-5 pb-10 sm:px-5">
    <p class="text-p-sm text-ink-gray-5">
      Ask Refteck about delivery dates, documents, quantities or anything else, and track the reply here.
      <span v-if="!isAdmin" class="text-ink-gray-6">You see only the queries you raised.</span>
    </p>
    <div class="mt-4"><FilterBar :filters="filterDefs" :model="f" :shown="filtered.length" :total="all.length" /></div>

    <div v-if="loading" class="mt-4 space-y-2">
      <Skeleton v-for="i in 5" :key="i" class="h-12 w-full rounded-4" />
    </div>
    <div v-else-if="filtered.length" class="mt-4 overflow-x-auto">
      <div class="min-w-[48rem]">
        <List :columns="['8rem', 'minmax(14rem,1fr)', '8rem', '9rem', '7rem', '9rem']" :row-height="52">
          <ListHeader>
            <ListHeaderCell>ID</ListHeaderCell>
            <ListHeaderCell>Subject</ListHeaderCell>
            <ListHeaderCell>Category</ListHeaderCell>
            <ListHeaderCell>Raised by</ListHeaderCell>
            <ListHeaderCell>Updated</ListHeaderCell>
            <ListHeaderCell>Status</ListHeaderCell>
          </ListHeader>
          <ListRows :items="filtered" v-slot="{ item }">
            <ListRow :route="`/queries/${item.name}`">
              <ListCell><span class="text-sm font-semibold text-[var(--rt-accent)] tabular-nums">{{ item.name }}</span></ListCell>
              <ListCell>
                <div class="min-w-0">
                  <div class="truncate text-base text-ink-gray-8">{{ item.subject }}</div>
                  <div v-if="item.related" class="truncate text-xs text-ink-gray-5">{{ item.related.name }}</div>
                </div>
              </ListCell>
              <ListCell><span class="text-sm text-ink-gray-7">{{ item.category }}</span></ListCell>
              <ListCell><span class="truncate text-sm text-ink-gray-7">{{ item.ownerName }}</span></ListCell>
              <ListCell><span class="text-sm text-ink-gray-5">{{ dayjs(item.updated).fromNow() }}</span></ListCell>
              <ListCell><Badge :label="item.status" :theme="themeFor(item.status)" variant="subtle" /></ListCell>
            </ListRow>
          </ListRows>
        </List>
      </div>
    </div>
    <EmptyState v-else title="No queries match these filters" text="Change the filters, or raise a new query." icon="lucide-message-circle-question">
      <Button v-if="!session.staff" variant="solid" theme="gray" icon-left="lucide-plus" label="Raise a query" class="rt-primary mt-2" @click="openNew()" />
    </EmptyState>
  </div>

  <Dialog v-model:open="show" title="Raise a query" size="lg">
    <div class="space-y-4">
      <FormControl v-model="form.subject" label="Subject" required :error="errors.subject" />
      <div class="grid gap-4 sm:grid-cols-2">
        <FormControl
          v-model="form.category"
          type="select"
          label="Category"
          :options="CATEGORIES.map((c) => ({ label: c, value: c }))"
        />
        <FormControl v-model="form.related" type="select" label="Related document" :options="relatedOptions" />
      </div>
      <FormControl v-model="form.text" type="textarea" label="Details" required :error="errors.text" :rows="5" />
      <div class="flex justify-end gap-2 pt-2">
        <Button label="Cancel" @click="show = false" />
        <Button variant="solid" theme="gray" label="Raise query" class="rt-primary" :loading="creating" @click="create" />
      </div>
    </div>
  </Dialog>
</template>
