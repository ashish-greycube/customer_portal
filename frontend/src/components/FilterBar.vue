<script setup lang="ts">
import { computed } from 'vue'
import { Button, DateRangePicker, FormControl, TextInput } from 'frappe-ui'

const props = defineProps<{ filters: any[]; model: Record<string, any>; shown?: number; total?: number }>()

const isSet = (v: any) => (Array.isArray(v) ? v.filter(Boolean).length > 0 : !!v)
const active = computed(() => props.filters.filter((f) => isSet(props.model[f.key])).length)

function clear() {
  for (const f of props.filters) props.model[f.key] = f.type === 'daterange' ? [] : ''
}
</script>

<template>
  <div class="rounded-5 border border-outline-gray-1 bg-surface-gray-1 p-3">
    <div class="flex flex-wrap items-end gap-3">
      <template v-for="f in filters" :key="f.key">
        <div v-if="f.type === 'search'" class="w-full sm:w-56">
          <TextInput v-model="model[f.key]" :label="f.label" :placeholder="f.placeholder">
            <template #prefix><span class="lucide-search size-4 text-ink-gray-5" aria-hidden="true" /></template>
          </TextInput>
        </div>
        <div v-else-if="f.type === 'daterange'" class="w-full sm:w-60">
          <DateRangePicker v-model="model[f.key]" :label="f.label" />
        </div>
        <div v-else class="w-[calc(50%-0.375rem)] sm:w-44">
          <FormControl v-model="model[f.key]" type="select" :label="f.label" :options="f.options" />
        </div>
      </template>
      <Button v-if="active" variant="ghost" icon-left="lucide-x" :label="`Clear ${active}`" @click="clear" />
      <span v-if="total !== undefined" class="ml-auto self-center text-sm text-ink-gray-5 tabular-nums">
        {{ shown === total ? `${total} records` : `${shown} of ${total}` }}
      </span>
    </div>
  </div>
</template>
