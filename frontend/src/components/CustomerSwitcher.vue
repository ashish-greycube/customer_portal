<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Combobox, toast } from 'frappe-ui'
import { BASE, api, errorText, session } from '../data'

// Staff view only: pick the customer whose portal you are looking at
const options = ref<{ label: string; value: string }[]>([])
const selected = ref<string | null>(session.customer?.id ?? null)

onMounted(async () => {
  try {
    options.value = await api('get_customers')
  } catch (e) {
    toast.error(errorText(e))
  }
})

async function change(value: any) {
  if (!value || value === session.customer?.id) return
  try {
    await api('set_customer', { customer: value })
    // Reload so every page starts from the new customer's data
    window.location.href = `${BASE}/`
  } catch (e) {
    toast.error(errorText(e))
    selected.value = session.customer?.id ?? null
  }
}
</script>

<template>
  <div class="px-3 pt-3">
    <p class="mb-1 flex items-center gap-1 px-1 text-xs text-ink-gray-5">
      <span class="lucide-eye size-3.5" aria-hidden="true" /> Staff view · customer
    </p>
    <Combobox
      v-model="selected"
      :options="options"
      placeholder="Search customers"
      aria-label="Customer"
      @update:model-value="change"
    />
  </div>
</template>
