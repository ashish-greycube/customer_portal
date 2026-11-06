<script setup lang="ts">
defineProps<{ title: string; text?: string; icon?: string }>()
</script>

<template>
  <div class="flex flex-col items-center justify-center gap-3 py-16 text-center">
    <div class="rounded-full bg-surface-gray-2 p-3 text-ink-gray-5">
      <span :class="[icon || 'lucide-inbox', 'size-6 block']" aria-hidden="true" />
    </div>
    <p class="text-base text-ink-gray-7">{{ title }}</p>
    <p v-if="text" class="text-sm text-ink-gray-5">{{ text }}</p>
    <slot />
  </div>
</template>
