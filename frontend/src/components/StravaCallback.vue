<template>
  <div class="strava-callback">
    <div class="callback-content">
      <div v-if="isLoading" class="loading">
        <i class="fa-solid fa-spinner fa-spin"></i>
        <p>{{ t('strava.completingLogin') }}</p>
      </div>

      <div v-else-if="error" class="error">
        <i class="fa-solid fa-exclamation-triangle"></i>
        <h3>{{ t('strava.loginError') }}</h3>
        <p>{{ error }}</p>
        <button @click="goToEditor" class="btn btn-primary">
          {{ t('common.continue') }}
        </button>
      </div>

      <div v-else class="success">
        <i class="fa-solid fa-check-circle"></i>
        <h3>{{ t('strava.loginSuccess') }}</h3>
        <p>{{ t('strava.redirecting') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useStravaApi } from '../composables/useStravaApi'

const { t } = useI18n()
const router = useRouter()
const { exchangeCode, isLoading, error } = useStravaApi()

const goToEditor = () => {
  router.push('/editor')
}

onMounted(async () => {
  try {
    const urlParams = new URLSearchParams(window.location.search)
    const code = urlParams.get('code')
    const error = urlParams.get('error')
    const state = urlParams.get('state')

    if (error) {
      throw new Error(`Strava authorization error: ${error}`)
    }

    if (!code) {
      throw new Error('No authorization code received from Strava')
    }

    await exchangeCode(code)
    console.info('Strava authentication successful')

    // Always redirect to home page to trigger navbar reload
    // Store the original destination in localStorage for later redirect
    if (state && state !== 'strava_auth') {
      localStorage.setItem('strava_redirect_after_auth', state)
    }

    console.info('Redirecting to home page to reload navbar')
    setTimeout(() => {
      window.location.href = '/' // Full page reload to refresh navbar
    }, 2000)
  } catch (err) {
    console.error('Strava callback error:', err)
  }
})
</script>

<style scoped>
.strava-callback {
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
