<script setup lang="ts">
import { PageHeader } from 'frappe-ui'
import UserMenu from './UserMenu.vue'
</script>

<template>
  <PageHeader>
    <div class="flex min-w-0 flex-1 items-center gap-2">
      <slot />
    </div>
    <div class="ml-3 flex shrink-0 items-center border-l border-outline-gray-2 pl-3">
      <UserMenu />
    </div>
  </PageHeader>
</template>
