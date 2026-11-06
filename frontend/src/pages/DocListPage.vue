<script setup lang="ts">
import AppHeader from '../components/AppHeader.vue'
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { toast } from 'frappe-ui'
import FilterBar from '../components/FilterBar.vue'
import RecordList from '../components/RecordList.vue'
import { api, errorText } from '../data'
import { DOCTYPES } from '../lib/doctypes'
import { inRange, matches, opts, ownerOpts, uniq } from '../lib/filters'
import { useSession } from '../lib/session'

const props = defineProps<{ doctype: string }>()
const route = useRoute()
const { isAdmin } = useSession()

const cfg = computed(() => DOCTYPES[props.doctype])
const rows = ref<any[]>([])
const all = computed(() => [...rows.value].sort((a, b) => b.date.localeCompare(a.date)))

const f = reactive<Record<string, any>>({ q: '', status: '', carrier: '', plant: '', owner: '', range: [] })
const loading = ref(true)

watch(
  () => props.doctype,
  async (doctype) => {
    loading.value = true
    rows.value = []
    try {
      const data = await api('get_records', { doctype })
      if (doctype === props.doctype) rows.value = data
    } catch (e) {
      toast.error(errorText(e))
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

watch(
  () => [props.doctype, route.query.status],
  () => Object.assign(f, { q: '', status: (route.query.status as string) || '', carrier: '', plant: '', owner: '', range: [] }),
  { immediate: true },
)

const filterDefs = computed(() => {
  const defs: any[] = [
    { key: 'q', label: 'Search', type: 'search', placeholder: 'ID, title or PO no.' },
    { key: 'status', label: 'Status', options: opts(cfg.value.statuses, 'All statuses') },
  ]
  if (cfg.value.carrier) defs.push({ key: 'carrier', label: 'Carrier', options: opts(uniq(all.value.map((r) => r.carrier)), 'All carriers') })
  defs.push({ key: 'plant', label: 'Plant', options: opts(uniq(all.value.map((r) => r.plant)), 'All plants') })
  if (isAdmin.value) defs.push({ key: 'owner', label: 'Raised by', options: ownerOpts() })
  defs.push({ key: 'range', label: cfg.value.dateLabel, type: 'daterange' })
  return defs
})

const filtered = computed(() =>
  all.value.filter(
    (r) =>
      matches(`${r.name} ${r.title} ${r.customerPo ?? ''}`, f.q) &&
      (!f.status || r.status === f.status) &&
      (!f.carrier || r.carrier === f.carrier) &&
      (!f.plant || r.plant === f.plant) &&
      (!f.owner || r.owner === f.owner) &&
      inRange(r.date, f.range),
  ),
)
</script>

<template>
  <AppHeader>
    <h1 class="text-2xl text-ink-gray-9">{{ cfg.label }}</h1>
  </AppHeader>

  <div class="space-y-4 px-3 pt-5 pb-10 sm:px-5">
    <p class="text-p-sm text-ink-gray-5">
      {{ cfg.description }}
      <span v-if="!isAdmin" class="text-ink-gray-6">You see only the records you raised.</span>
    </p>
    <FilterBar :filters="filterDefs" :model="f" :shown="filtered.length" :total="all.length" />
    <RecordList
      :rows="filtered"
      :fields="cfg.fields"
      :loading="loading"
      :route-for="(r) => `/print/${doctype}/${r.name}`"
      :empty-title="`No ${cfg.label.toLowerCase()} match these filters`"
      empty-text="Change or clear the filters above."
    />
  </div>
</template>
