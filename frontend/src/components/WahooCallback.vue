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
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useWahooApi } from '../composables/useWahooApi'

const { t } = useI18n()
const router = useRouter()
const { exchangeCode, isLoading, error } = useWahooApi()

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

    await exchangeCode(code)
    // User information is already included in the exchangeCode response

    // Check if we have a redirect URL in sessionStorage
    const redirectUrl = sessionStorage.getItem('wahoo_redirect_after_auth')

    if (redirectUrl) {
      sessionStorage.removeItem('wahoo_redirect_after_auth')
      setTimeout(() => {
        window.location.href = redirectUrl // Redirect to original page
      }, 2000)
    } else {
      // Default to home page to reload navbar
      setTimeout(() => {
        window.location.href = '/' // Full page reload to refresh navbar
      }, 2000)
    }
  } catch (err) {
    console.error('Wahoo callback error:', err)
  }
})
</script>

<style scoped>
.wahoo-callback {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: var(--bg-secondary);
  transition: background-color 0.3s ease;
}

.callback-content {
  text-align: center;
  max-width: 400px;
  padding: 2rem;
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--card-border);
  transition: all 0.3s ease;
}

.loading i,
.success i,
.error i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.loading i {
  color: var(--status-info);
}

.success i {
  color: var(--status-success);
}

.error i {
  color: var(--status-error);
}

h3 {
  margin: 0 0 1rem 0;
  color: var(--text-primary);
  font-size: 1.5rem;
  font-weight: 600;
}

p {
  margin: 0 0 1.5rem 0;
  color: var(--text-tertiary);
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
  background: var(--button-primary-bg);
  color: var(--button-primary-text);
}

.btn-primary:hover {
  background: var(--button-primary-hover);
}
</style>
