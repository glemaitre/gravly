<template>
  <div class="wahoo-callback">
    <div class="callback-content">
      <div v-if="isLoading" class="loading">
        <i class="fa-solid fa-spinner fa-spin"></i>
        <p>{{ t('wahoo.completingLogin') }}</p>
      </div>

      <div v-else-if="error" class="error">
        <i class="fa-solid fa-exclamation-triangle"></i>
        <h3>{{ t('wahoo.loginError') }}</h3>
        <p>{{ error }}</p>
        <button @click="goToHome" class="btn btn-primary">
          {{ t('common.continue') }}
        </button>
      </div>

      <div v-else class="success">
        <i class="fa-solid fa-check-circle"></i>
        <h3>{{ t('wahoo.loginSuccess') }}</h3>
        <p>{{ t('wahoo.redirecting') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()
const isLoading = ref(true)
const error = ref<string | null>(null)

const goToHome = () => {
  router.push('/')
}

onMounted(async () => {
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    const errorParam = urlParams.get('error')

    if (errorParam) {
      throw new Error(`Wahoo authorization error: ${errorParam}`)
    }

    if (!code) {
      throw new Error('No authorization code received from Wahoo')
    }

    // Call the backend API to handle the code
    const response = await fetch(`/api/wahoo/callback?code=${encodeURIComponent(code)}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`)
    }

    const result = await response.json()
    console.info('Wahoo authentication successful:', result)

    // Set loading to false to show success state
    isLoading.value = false

    // Redirect to home page after a short delay
    setTimeout(() => {
      window.location.href = '/' // Full page reload to refresh navbar
    }, 2000)
  } catch (err) {
    console.error('Wahoo callback error:', err)
    error.value = err instanceof Error ? err.message : 'Unknown error occurred'
    isLoading.value = false
  }
})
</script>

<style scoped>
.wahoo-callback {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f9fafb;
}

.callback-content {
  text-align: center;
  max-width: 400px;
  padding: 2rem;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.loading i,
.success i,
.error i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.loading i {
  color: #3b82f6;
}

.success i {
  color: #10b981;
}

.error i {
  color: #ef4444;
}

h3 {
  margin: 0 0 1rem 0;
  color: #1f2937;
  font-size: 1.5rem;
  font-weight: 600;
}

p {
  margin: 0 0 1.5rem 0;
  color: #6b7280;
  line-height: 1.5;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover {
  background: #2563eb;
}
</style>
