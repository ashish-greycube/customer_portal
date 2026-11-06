<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { STEPS } from '../data'

// links: a route per step, or null when that step has no document yet.
// viewing: the step whose document is open on this page.
const props = defineProps<{ step: number; links?: (string | null)[]; viewing?: number }>()

const circle = (n: number) =>
  n < props.step
    ? 'bg-[var(--rt-navy)] text-[#fff] border border-[var(--rt-navy)]'
    : n === props.step
      ? 'bg-[var(--rt-orange-soft)] text-[var(--rt-orange-ink)] border-2 border-[var(--rt-orange)] font-semibold'
      : 'bg-surface-base text-ink-gray-4 border border-outline-gray-2'

const linkFor = (i: number) => (props.viewing === i + 1 ? null : props.links?.[i] ?? null)
</script>

<template>
  <ol class="grid grid-cols-6" :aria-label="`Workflow step ${step} of ${STEPS.length}: ${STEPS[step - 1]}`">
    <li v-for="(label, i) in STEPS" :key="label" class="relative flex flex-col items-center px-1 text-center">
      <div
        v-if="i > 0"
        class="absolute top-3.5 right-1/2 w-full border-t-2"
        :class="i + 1 <= step ? 'border-[var(--rt-navy)]' : 'border-outline-gray-2'"
      />
      <component
        :is="linkFor(i) ? RouterLink : 'div'"
        :to="linkFor(i) || undefined"
        class="group relative z-10 flex flex-col items-center rounded-4 px-1"
        :class="linkFor(i) ? 'cursor-pointer' : ''"
        :title="linkFor(i) ? `Open ${label.toLowerCase()} document` : undefined"
      >
        <div
          class="flex size-7 items-center justify-center rounded-full text-xs tabular-nums transition"
          :class="[circle(i + 1), linkFor(i) ? 'group-hover:ring-4 group-hover:ring-[var(--rt-navy-soft)]' : '', viewing === i + 1 ? 'ring-4 ring-[var(--rt-orange-soft)]' : '']"
        >
          <span v-if="i + 1 < step" class="lucide-check size-3.5" aria-hidden="true" />
          <span v-else>{{ i + 1 }}</span>
        </div>
        <span
          class="mt-2 text-xs leading-tight"
          :class="[
            i + 1 === step ? 'text-[var(--rt-orange-ink)] font-semibold' : i + 1 < step ? 'text-[var(--rt-accent)]' : 'text-ink-gray-4',
            linkFor(i) ? 'underline decoration-dotted underline-offset-4 group-hover:decoration-solid' : '',
          ]"
        >
          {{ label }}
        </span>
        <span v-if="viewing === i + 1" class="mt-1 text-2xs text-ink-gray-5">Viewing</span>
      </component>
    </li>
  </ol>
</template>
