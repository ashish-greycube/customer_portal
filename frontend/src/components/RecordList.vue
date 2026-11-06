<script setup lang="ts">
import { Badge, Skeleton } from 'frappe-ui'
import { List, ListHeader, ListHeaderCell, ListRows, ListRow, ListCell } from 'frappe-ui/list'
import { STEPS } from '../data'
import { fmtDate, fmtMoney, themeFor } from '../lib/format'
import EmptyState from './EmptyState.vue'

defineProps<{
  rows: any[]
  fields: any[]
  routeFor?: (row: any) => string
  loading?: boolean
  emptyTitle?: string
  emptyText?: string
}>()
</script>

<template>
  <div v-if="loading" class="space-y-2">
    <Skeleton v-for="i in 6" :key="i" class="h-10 w-full rounded-4" />
  </div>
  <div v-else-if="rows.length" class="overflow-x-auto">
    <div class="min-w-[56rem]">
      <List :columns="fields.map((f) => f.width)" :row-height="48">
        <ListHeader>
          <ListHeaderCell v-for="f in fields" :key="f.key" :class="f.type === 'money' ? 'justify-end' : ''">
            {{ f.label }}
          </ListHeaderCell>
        </ListHeader>
        <ListRows :items="rows" v-slot="{ item }">
          <ListRow :route="routeFor ? routeFor(item) : undefined">
            <ListCell v-for="f in fields" :key="f.key" :class="f.type === 'money' ? 'justify-end' : ''">
              <span v-if="f.type === 'id'" class="truncate text-sm font-semibold text-[var(--rt-accent)] tabular-nums">{{ item[f.key] }}</span>
              <span v-else-if="f.type === 'title'" class="truncate text-base text-ink-gray-8">{{ item[f.key] }}</span>
              <span v-else-if="f.type === 'date'" class="text-sm text-ink-gray-6 tabular-nums">{{ fmtDate(item[f.key]) }}</span>
              <span v-else-if="f.type === 'money'" class="text-sm text-ink-gray-8 tabular-nums">{{ fmtMoney(item[f.key], item.currency) }}</span>
              <Badge v-else-if="f.type === 'status'" :label="item[f.key]" :theme="themeFor(item[f.key])" variant="subtle" />
              <div v-else-if="f.type === 'step'" class="flex min-w-0 items-center gap-2">
                <span class="flex shrink-0 gap-0.5" aria-hidden="true">
                  <span
                    v-for="n in 6"
                    :key="n"
                    class="h-1.5 w-2 rounded-full"
                    :class="n < item.step ? 'bg-[var(--rt-navy)]' : n === item.step ? 'bg-[var(--rt-orange)]' : 'bg-surface-gray-3'"
                  />
                </span>
                <span class="truncate text-sm text-ink-gray-7">{{ STEPS[item.step - 1] }}</span>
              </div>
              <span v-else class="truncate text-sm text-ink-gray-7">{{ item[f.key] }}</span>
            </ListCell>
          </ListRow>
        </ListRows>
      </List>
    </div>
  </div>
  <EmptyState v-else :title="emptyTitle || 'Nothing here yet'" :text="emptyText" />
</template>
