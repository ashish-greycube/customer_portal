<script setup lang="ts">
import AppHeader from '../components/AppHeader.vue'
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Alert, Button, DatePicker, Dialog, FileUploader, FormControl, toast } from 'frappe-ui'
import dayjs from 'dayjs'
import FilterBar from '../components/FilterBar.vue'
import RecordList from '../components/RecordList.vue'
import { DOCTYPES } from '../lib/doctypes'
import { inRange, matches, opts, ownerOpts, uniq } from '../lib/filters'
import { fmtDate, fmtMoney } from '../lib/format'
import { api, errorText, session } from '../data'
import { useSession } from '../lib/session'

const route = useRoute()
const router = useRouter()
const { isAdmin } = useSession()
const cfg = DOCTYPES['po-submission']

const pos = ref<any[]>([])
const quotes = ref<any[]>([])
const list = computed(() => [...pos.value].sort((a, b) => b.date.localeCompare(a.date)))
const openQuotes = computed(() => quotes.value.filter((q) => q.status === 'Open'))
const loading = ref(true)
const submitting = ref(false)

async function load() {
  try {
    ;[pos.value, quotes.value] = await Promise.all([
      api('get_records', { doctype: 'po-submission' }),
      api('get_records', { doctype: 'quotation' }),
    ])
  } catch (e) {
    toast.error(errorText(e))
  } finally {
    loading.value = false
  }
}

const f = reactive<Record<string, any>>({ q: '', status: '', plant: '', owner: '', range: [] })
const filterDefs = computed(() => [
  { key: 'q', label: 'Search', type: 'search', placeholder: 'PO no., title or quotation' },
  { key: 'status', label: 'Status', options: opts(cfg.statuses, 'All statuses') },
  { key: 'plant', label: 'Plant', options: opts(uniq(list.value.map((r) => r.plant)), 'All plants') },
  ...(isAdmin.value ? [{ key: 'owner', label: 'Uploaded by', options: ownerOpts() }] : []),
  { key: 'range', label: cfg.dateLabel, type: 'daterange' },
])
const filtered = computed(() =>
  list.value.filter(
    (r) =>
      matches(`${r.customerPo} ${r.title} ${r.quotation}`, f.q) &&
      (!f.status || r.status === f.status) &&
      (!f.plant || r.plant === f.plant) &&
      (!f.owner || r.uploadedBy === f.owner) &&
      inRange(r.date, f.range),
  ),
)

const show = ref(false)
const blank = () => ({ quotation: '', customerPo: '', poDate: dayjs().format('YYYY-MM-DD'), fileName: '', fileUrl: '', remarks: '' })
const form = ref(blank())
const errors = ref<Record<string, string>>({})
const selected = computed(() => openQuotes.value.find((q) => q.name === form.value.quotation))

function open(quotation = '') {
  form.value = { ...blank(), quotation: quotation || openQuotes.value[0]?.name || '' }
  errors.value = {}
  show.value = true
}

onMounted(async () => {
  await load()
  if (route.query.quotation && !session.staff) open(route.query.quotation as string)
})

function onUploaded(file: any) {
  form.value.fileName = file.file_name || file.name || 'purchase-order.pdf'
  form.value.fileUrl = file.file_url
  errors.value.file = ''
}

async function submit() {
  const e: Record<string, string> = {}
  if (!form.value.quotation) e.quotation = 'Choose the quotation this PO is for'
  if (!form.value.customerPo.trim()) e.customerPo = 'Enter your PO number'
  if (!form.value.fileUrl) e.file = 'Attach the PO document'
  errors.value = e
  if (Object.keys(e).length) return
  submitting.value = true
  try {
    await api('submit_po', {
      quotation: form.value.quotation,
      customer_po: form.value.customerPo,
      po_date: form.value.poDate,
      file_url: form.value.fileUrl,
      remarks: form.value.remarks,
    })
    show.value = false
    router.replace('/po-submission')
    toast.success('PO submitted. Refteck will confirm it shortly.')
    loading.value = true
    await load()
  } catch (err) {
    toast.error(errorText(err))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <AppHeader>
    <h1 class="text-2xl text-ink-gray-9">PO submission</h1>
    <Button v-if="!session.staff" variant="solid" theme="gray" icon-left="lucide-upload" label="Submit PO" class="rt-primary ml-auto" @click="open()" />
  </AppHeader>

  <div class="space-y-4 px-3 pt-5 pb-10 sm:px-5">
    <p class="text-p-sm text-ink-gray-5">
      Upload your purchase order against an open quotation. Refteck checks it, confirms it and creates a sales order.
    </p>
    <FilterBar :filters="filterDefs" :model="f" :shown="filtered.length" :total="list.length" />
    <RecordList
      :rows="filtered"
      :fields="cfg.fields"
      :loading="loading"
      :route-for="(r) => `/print/po-submission/${r.name}`"
      empty-title="No POs match these filters"
      empty-text="Change the filters, or submit a PO against an open quotation."
    />
  </div>

  <Dialog v-model:open="show" title="Submit purchase order" size="lg">
    <div v-if="!openQuotes.length" class="space-y-4">
      <Alert title="No open quotations" description="You can submit a PO once Refteck sends you a quotation." theme="amber" />
      <div class="flex justify-end"><Button label="Close" @click="show = false" /></div>
    </div>
    <div v-else class="space-y-4">
      <FormControl
        v-model="form.quotation"
        type="select"
        label="Quotation"
        required
        :error="errors.quotation"
        :options="openQuotes.map((q) => ({ label: `${q.name} · ${q.title}`, value: q.name }))"
        :description="selected ? `Grand total ${fmtMoney(selected.amount, selected.currency)}${selected.validTill ? ` · valid till ${fmtDate(selected.validTill)}` : ''}` : ''"
      />
      <div class="grid gap-4 sm:grid-cols-2">
        <FormControl v-model="form.customerPo" label="Customer PO no." required :error="errors.customerPo" />
        <DatePicker v-model="form.poDate" label="PO date" />
      </div>
      <div>
        <p class="mb-1.5 text-xs text-ink-gray-6">PO document <span class="text-ink-red-5">*</span></p>
        <FileUploader :file-types="['.pdf', '.png', '.jpg', '.jpeg', '.doc', '.docx']" :private="true" @success="onUploaded" @failure="() => toast.error('Upload failed. Try again.')">
          <template #default="{ uploading, progress, openFileSelector }">
            <div class="flex items-center gap-3 rounded-4 border border-dashed border-outline-gray-3 px-3 py-3">
              <span class="lucide-file-up size-5 text-ink-gray-5" aria-hidden="true" />
              <div class="min-w-0 flex-1">
                <div class="truncate text-sm text-ink-gray-8">{{ form.fileName || 'PDF, image or Word, up to 10 MB' }}</div>
                <div v-if="uploading" class="text-xs text-ink-gray-5">Uploading {{ progress }}%</div>
              </div>
              <Button :label="form.fileName ? 'Replace' : 'Choose file'" :loading="uploading" @click="openFileSelector" />
            </div>
          </template>
        </FileUploader>
        <p v-if="errors.file" class="mt-1.5 text-xs text-ink-red-5">{{ errors.file }}</p>
      </div>
      <FormControl v-model="form.remarks" type="textarea" label="Remarks" description="Optional. Anything Refteck should know about this PO." />
      <div class="flex justify-end gap-2 pt-2">
        <Button label="Cancel" @click="show = false" />
        <Button variant="solid" theme="gray" label="Submit PO" class="rt-primary" :loading="submitting" @click="submit" />
      </div>
    </div>
  </Dialog>
</template>
