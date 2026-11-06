<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { Button, FormControl, Password, call, toast } from 'frappe-ui'
import { BASE, errorText } from '../data'

const route = useRoute()
const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function signIn() {
  error.value = ''
  if (!email.value.trim()) {
    error.value = 'Enter your email or username'
    return
  }
  if (!password.value) {
    error.value = 'Enter your password'
    return
  }
  loading.value = true
  try {
    await call('login', { usr: email.value.trim(), pwd: password.value })
    // Full reload so the page picks up the new session and CSRF token
    const to = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    window.location.href = BASE + to
  } catch (e) {
    error.value = errorText(e) === 'Something went wrong' ? 'Incorrect email or password' : errorText(e)
    loading.value = false
  }
}

async function forgot() {
  if (!email.value.trim()) {
    toast.error('Enter your email first')
    return
  }
  try {
    await call('frappe.core.doctype.user.user.reset_password', { user: email.value.trim() })
    toast.success(`Reset link sent to ${email.value.trim()}`)
  } catch (e) {
    toast.error(errorText(e))
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-[var(--rt-backdrop)] px-4">
    <div class="w-full max-w-sm">
      <div class="mb-6 text-center">
        <div class="text-3xl font-bold tracking-[.06em] text-[var(--rt-accent)]">REFTECK</div>
        <div class="rt-tricolor mx-auto mt-2 h-[3px] w-12 rounded-full" />
        <h1 class="mt-5 text-2xl text-ink-gray-9">Sign in to the customer portal</h1>
        <p class="mt-1 text-p-sm text-ink-gray-5">Opportunities, quotations, orders and shipping in one place</p>
      </div>
      <form class="space-y-4 overflow-hidden rounded-6 border border-outline-gray-1 border-t-4 border-t-[var(--rt-navy)] bg-surface-base p-6 shadow-sm" @submit.prevent="signIn">
        <FormControl v-model="email" type="text" label="Email or username" autocomplete="username" required />
        <Password v-model="password" label="Password" :error="error" required />
        <div class="flex justify-end">
          <Button variant="ghost" size="sm" label="Forgot password?" @click="forgot" />
        </div>
        <Button type="submit" variant="solid" theme="gray" label="Sign in" class="rt-primary w-full" :loading="loading" />
      </form>
      <p class="mt-6 text-center text-p-xs text-ink-gray-5">Need access? Ask <a href="mailto:abc@refteck.in" class="font-semibold text-[var(--rt-link)]">abc@refteck.in</a></p>
    </div>
  </div>
</template>
