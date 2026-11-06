<script setup lang="ts">
import AppHeader from '../components/AppHeader.vue'
import { computed, ref, watch } from 'vue'
import { Badge, Breadcrumbs, Button, Skeleton, Tooltip, toast } from 'frappe-ui'
import EmptyState from '../components/EmptyState.vue'
import WorkflowSteps from '../components/WorkflowSteps.vue'
import { STEPS, api, contactName, session } from '../data'
import { DOCTYPES } from '../lib/doctypes'
import { fmtDate, fmtMoney, fmtQty, themeFor } from '../lib/format'

const props = defineProps<{ doctype: string; name: string }>()

const CUSTOMER = session.customer
const cfg = computed(() => DOCTYPES[props.doctype])
const doc = ref<any>(null)
const loading = ref(true)

watch(
  () => [props.doctype, props.name],
  async () => {
    loading.value = true
    try {
      doc.value = await api('get_document', { doctype: props.doctype, name: props.name })
    } catch {
      doc.value = null
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

const step = computed(() => doc.value?.step ?? 1)
const links = computed(() => doc.value?.links ?? [])
const viewing = computed(
  () => ({ opportunity: 1, quotation: 2, 'po-submission': 3, 'sales-order': 4, 'sales-invoice': step.value >= 6 ? 6 : 5 })[props.doctype],
)
const canSubmitPO = computed(() => !session.staff && props.doctype === 'quotation' && doc.value?.status === 'Open')
const queryRoute = computed(() => `/queries?new=1&related=${encodeURIComponent(`${props.doctype}|${props.name}`)}`)
const showPrices = computed(() => props.doctype !== 'opportunity')
const isPO = computed(() => props.doctype === 'po-submission')
const fileName = computed(() => (isPO.value ? doc.value?.file?.split('/').pop() : `${props.name}.pdf`))
const currency = computed(() => doc.value?.totals?.currency || doc.value?.currency)
const money = (n: number) => fmtMoney(n, currency.value)
const contactLine = computed(() =>
  doc.value ? [doc.value.plant && `Plant: ${doc.value.plant}`, doc.value.ownerName && `Contact: ${doc.value.ownerName}`].filter(Boolean).join(' · ') : '',
)

const meta = computed(() => {
  const d = doc.value
  if (!d) return []
  const byType: Record<string, string[][]> = {
    opportunity: [['Opportunity', d.name], ['Date', fmtDate(d.date)], ['Required by', fmtDate(d.requiredBy)], ['Raised by', d.ownerName || '—']],
    quotation: [['Quotation', d.name], ['Date', fmtDate(d.date)], ['Valid till', fmtDate(d.validTill)], ['Against', d.opportunity || '—']],
    'po-submission': [['Customer PO no.', d.customerPo], ['PO date', fmtDate(d.date)], ['Against quotation', d.quotation], ['Uploaded by', contactName(d.uploadedBy) || '—']],
    'sales-order': [['Sales order', d.name], ['Order date', fmtDate(d.date)], ['Customer PO', d.customerPo || '—'], ['Expected delivery', fmtDate(d.deliveryDate)]],
    'sales-invoice': [['Invoice', `${d.name} (${d.docstatus})`], ['Invoice date', fmtDate(d.date)], ['Sales order', d.salesOrder || '—'], ['Carrier · AWB', d.dispatch]],
  }
  return [...byType[props.doctype], ['Workflow step', `${step.value} of ${STEPS.length} · ${STEPS[step.value - 1]}`], ['Status', d.status]]
})

const pdfUrl = (inline = false) => {
  const q = new URLSearchParams({ doctype: props.doctype, name: props.name, ...(inline ? { inline: '1' } : {}) })
  return isPO.value
    ? `/api/method/customer_portal.api.download_po_file?${new URLSearchParams({ name: props.name })}`
    : `/api/method/customer_portal.api.download_pdf?${q}`
}

function download() {
  window.location.href = pdfUrl()
  toast.success(`Downloading ${fileName.value}`)
}
const openTab = () => window.open(pdfUrl(true), '_blank')
const print = () => window.print()

const zoom = ref(1)
const setZoom = (d: number) => (zoom.value = Math.min(1.5, Math.max(0.5, +(zoom.value + d).toFixed(2))))
</script>

<template>
  <AppHeader>
    <Breadcrumbs :items="[{ label: cfg?.label ?? 'Documents', route: { path: cfg?.path ?? '/' } }, { label: name }]" />
    <div v-if="doc" class="ml-auto flex gap-2">
      <Button v-if="!session.staff" variant="subtle" icon-left="lucide-message-circle-question" label="Raise query" :route="queryRoute" />
      <Button v-if="canSubmitPO" variant="subtle" icon-left="lucide-download" label="Download PDF" @click="download" />
      <Button v-else variant="solid" theme="gray" class="rt-primary" icon-left="lucide-download" :label="isPO ? 'Download PO' : 'Download PDF'" @click="download" />
      <Button
        v-if="canSubmitPO"
        variant="solid"
        theme="gray"
        class="rt-highlight"
        icon-left="lucide-upload"
        label="Submit PO"
        :route="`/po-submission?quotation=${doc.name}`"
      />
    </div>
  </AppHeader>

  <div v-if="loading" class="mx-auto max-w-[900px] space-y-4 px-3 pt-5 sm:px-5">
    <Skeleton class="h-28 w-full rounded-5" />
    <Skeleton class="h-[32rem] w-full rounded-5" />
  </div>
  <EmptyState v-else-if="!doc" title="Document not available" text="It does not exist or belongs to another contact." icon="lucide-lock" />

  <div v-else class="px-3 pt-5 pb-12 sm:px-5">
    <div class="mx-auto max-w-[900px] space-y-4">
      <!-- Next action on an open quotation -->
      <section
        v-if="canSubmitPO"
        class="flex flex-wrap items-center gap-3 rounded-5 border border-[var(--rt-orange)] bg-[var(--rt-orange-soft)] px-4 py-3"
      >
        <span class="lucide-file-up size-5 text-[var(--rt-orange-ink)]" aria-hidden="true" />
        <div class="min-w-0 flex-1">
          <div class="text-base font-semibold text-[var(--rt-orange-ink)]">Ready for your purchase order</div>
          <div class="text-sm text-ink-gray-7"><template v-if="doc.validTill">Valid till {{ fmtDate(doc.validTill) }}. </template> Submit your PO to move this to step 3, PO upload.</div>
        </div>
        <Button variant="solid" theme="gray" class="rt-highlight" size="md" icon-left="lucide-upload" label="Submit PO" :route="`/po-submission?quotation=${doc.name}`" />
      </section>

      <!-- Workflow, shown once at the top. Each reached step opens its document. -->
      <section class="rounded-5 border border-outline-gray-1 bg-surface-base px-5 pt-4 pb-5">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div class="text-sm text-ink-gray-6">
            {{ cfg.singular }} · <span class="tabular-nums">{{ name }}</span> · current step
            <span class="tabular-nums">{{ step }} of {{ STEPS.length }}</span> ·
            <span class="font-semibold text-[var(--rt-orange-ink)]">{{ STEPS[step - 1] }}</span>
          </div>
          <Badge :label="doc.status" :theme="themeFor(doc.status)" variant="subtle" />
        </div>
        <WorkflowSteps :step="step" :links="links" :viewing="viewing" />
      </section>

      <!-- PDF viewer -->
      <section class="overflow-hidden rounded-5 border border-outline-gray-2">
        <div class="flex items-center gap-2 bg-[var(--rt-navy)] px-3 py-2 text-[#fff]">
          <span class="lucide-file-text size-4 opacity-80" aria-hidden="true" />
          <span class="truncate text-sm font-medium">{{ fileName }}</span>
          <span class="text-xs opacity-70">{{ isPO ? 'Uploaded PO' : 'Summary' }}</span>
          <div class="ml-auto flex items-center gap-1">
            <Tooltip text="Zoom out"><button type="button" class="rounded-4 p-1.5 hover:bg-[#ffffff22]" aria-label="Zoom out" @click="setZoom(-0.1)"><span class="lucide-zoom-out block size-4" /></button></Tooltip>
            <span class="w-11 text-center text-xs tabular-nums">{{ Math.round(zoom * 100) }}%</span>
            <Tooltip text="Zoom in"><button type="button" class="rounded-4 p-1.5 hover:bg-[#ffffff22]" aria-label="Zoom in" @click="setZoom(0.1)"><span class="lucide-zoom-in block size-4" /></button></Tooltip>
            <span class="mx-1 h-4 border-l border-[#ffffff44]" />
            <Tooltip :text="isPO ? 'Open PO in new tab' : 'Open official PDF in new tab'"><button type="button" class="rounded-4 p-1.5 hover:bg-[#ffffff22]" aria-label="Open PDF in new tab" @click="openTab"><span class="lucide-external-link block size-4" /></button></Tooltip>
            <Tooltip text="Print"><button type="button" class="rounded-4 p-1.5 hover:bg-[#ffffff22]" aria-label="Print" @click="print"><span class="lucide-printer block size-4" /></button></Tooltip>
            <Tooltip :text="isPO ? 'Download PO' : 'Download official PDF'"><button type="button" class="rounded-4 p-1.5 hover:bg-[#ffffff22]" aria-label="Download PDF" @click="download"><span class="lucide-download block size-4" /></button></Tooltip>
          </div>
        </div>

        <div class="overflow-auto bg-[var(--rt-backdrop)] p-6">
          <div class="mx-auto w-fit">
            <!-- A4 page that grows with the item count. Fixed paper colours, like the PDF file. -->
            <div
              class="flex min-h-[1123px] w-[794px] flex-col bg-[#fff] text-[12px] text-[#13213a] shadow-lg"
              :style="{ zoom }"
            >
              <div class="flex items-start justify-between bg-[#182a4f] px-[53px] pt-[26px] pb-[20px] text-[#fff]">
                <div>
                  <div class="text-[24px] font-bold tracking-[.06em]">REFTECK</div>
                  <div class="mt-1 text-[10px] text-[#c3cddb]">{{ session.company.line }}</div>
                </div>
                <div class="text-right">
                  <div class="text-[21px] font-bold">{{ cfg.singular }}</div>
                  <div class="mt-1 text-[12px] text-[#c3cddb]">{{ name }}</div>
                </div>
              </div>
              <div class="flex h-[5px]"><div class="flex-1 bg-[#ed7923]" /><div class="flex-1 bg-[#268c42]" /><div class="flex-1 bg-[#182a4f]" /></div>

              <div class="flex-1 px-[53px] pt-[32px]">
                <div class="flex justify-between gap-8">
                  <div class="w-[300px]">
                    <div class="text-[10px] text-[#66758c]">Customer</div>
                    <div class="mt-1 text-[15px] font-bold">{{ CUSTOMER.name }}</div>
                    <div class="mt-1 text-[11px] leading-snug text-[#66758c]">{{ doc.address || CUSTOMER.address }}</div>
                    <div class="mt-2 text-[11px] text-[#66758c]">{{ contactLine }}</div>
                  </div>
                  <dl class="grid w-[300px] grid-cols-2 gap-x-4 gap-y-3">
                    <div v-for="[k, v] in meta" :key="k">
                      <dt class="text-[10px] text-[#66758c]">{{ k }}</dt>
                      <dd class="mt-0.5 font-semibold tabular-nums">{{ v }}</dd>
                    </div>
                  </dl>
                </div>

                <div class="mt-8 text-[15px] font-bold text-[#182a4f]">{{ doc.title }}</div>
                <table class="mt-3 w-full">
                  <thead>
                    <tr class="bg-[#e9edf5] text-left text-[11px] text-[#66758c]">
                      <th class="py-2 pr-2 pl-[10px] font-normal">#</th>
                      <th class="py-2 pr-2 font-normal">Item</th>
                      <th class="py-2 pr-2 text-right font-normal">Qty</th>
                      <th class="py-2 pr-2 font-normal">UOM</th>
                      <th v-if="showPrices" class="py-2 pr-2 text-right font-normal">Rate</th>
                      <th v-if="showPrices" class="py-2 pr-[10px] text-right font-normal">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="it in doc.items" :key="it.idx" class="border-b border-[#dce2ea] align-top">
                      <td class="py-2.5 pr-2 pl-[10px] text-[#66758c] tabular-nums">{{ it.idx }}</td>
                      <td class="py-2.5 pr-2">
                        <div>{{ it.description }}</div>
                        <div class="text-[10px] text-[#66758c]">{{ it.code }}</div>
                      </td>
                      <td class="py-2.5 pr-2 text-right tabular-nums">{{ fmtQty(it.qty) }}</td>
                      <td class="py-2.5 pr-2 text-[#66758c]">{{ it.uom }}</td>
                      <td v-if="showPrices" class="py-2.5 pr-2 text-right tabular-nums">{{ money(it.rate) }}</td>
                      <td v-if="showPrices" class="py-2.5 pr-[10px] text-right tabular-nums">{{ money(it.amount) }}</td>
                    </tr>
                  </tbody>
                </table>

                <div v-if="showPrices && doc.totals" class="mt-4 flex justify-end">
                  <dl class="w-[240px] space-y-1.5">
                    <div class="flex justify-between"><dt class="text-[#66758c]">Net total</dt><dd class="tabular-nums">{{ money(doc.totals.net) }}</dd></div>
                    <div v-if="doc.totals.discount" class="flex justify-between"><dt class="text-[#66758c]">Discount</dt><dd class="tabular-nums">−{{ money(doc.totals.discount) }}</dd></div>
                    <div class="flex justify-between"><dt class="text-[#66758c]">Taxes &amp; charges</dt><dd class="tabular-nums">{{ money(doc.totals.taxes) }}</dd></div>
                    <div class="flex justify-between border-t border-[#dce2ea] pt-2 text-[14px] font-bold text-[#182a4f]">
                      <dt>Grand total</dt><dd class="tabular-nums">{{ money(doc.totals.grand) }}</dd>
                    </div>
                  </dl>
                </div>
              </div>

              <div class="mx-[53px] flex justify-between gap-6 border-t border-[#dce2ea] pt-3 pb-[40px] text-[10px] text-[#66758c]">
                <span class="line-clamp-3 whitespace-pre-line">{{ doc.terms || (isPO ? `Quotation items shown. Your uploaded PO: ${fileName}` : 'Summary view. Download the PDF for the official document.') }}</span>
                <span class="shrink-0">{{ session.company.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>
