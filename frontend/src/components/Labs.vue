<template>
  <div class="labs-page">
    <div class="labs-container">
      <header class="labs-header">
        <h1 class="labs-title">
          <i class="fa-solid fa-flask"></i>
          {{ $t('labs.title') }}
        </h1>
        <p class="labs-description">
          {{ $t('labs.description') }}
        </p>
      </header>

      <section class="labs-content">
        <div class="labs-section">
          <h2 class="section-title">
            <i class="fa-solid fa-cloud"></i>
            {{ $t('labs.wahooIntegration.title') }}
          </h2>
          <p class="section-description">
            {{ $t('labs.wahooIntegration.description') }}
          </p>

          <div class="wahoo-auth-section">
            <div class="auth-status" v-if="wahooAuthStatus">
              <div class="status-indicator" :class="wahooAuthStatus.status">
                <i :class="wahooAuthStatus.icon"></i>
                <span>{{ wahooAuthStatus.message }}</span>
              </div>
            </div>

            <button
              class="btn btn-primary wahoo-auth-btn"
              @click="handleWahooAuthorization"
              :disabled="isLoadingWahooAuth"
            >
              <i class="fa-solid fa-external-link-alt"></i>
              <span v-if="!isLoadingWahooAuth">{{
                $t('labs.wahooIntegration.authorizeButton')
              }}</span>
              <span v-else>{{ $t('labs.wahooIntegration.authorizing') }}</span>
            </button>
          </div>
        </div>

        <div class="labs-section">
          <h2 class="section-title">
            <i class="fa-solid fa-info-circle"></i>
            {{ $t('labs.info.title') }}
          </h2>
          <div class="info-content">
            <p>{{ $t('labs.info.description') }}</p>
            <ul class="info-list">
              <li>{{ $t('labs.info.feature1') }}</li>
              <li>{{ $t('labs.info.feature2') }}</li>
              <li>{{ $t('labs.info.feature3') }}</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, watch } from 'vue'
import { useAuthorization } from '../composables/useAuthorization'
import { useWahooApi } from '../composables/useWahooApi'

// Authorization check
const { isAuthorized, isLoadingAuthorization } = useAuthorization()

// Wahoo API composable
const { getAuthUrl, isLoading: isLoadingWahooAuth } = useWahooApi()

// Wahoo authorization state
const wahooAuthStatus = ref<{
  status: 'success' | 'error' | 'info'
  message: string
  icon: string
} | null>(null)

/**
 * Handle Wahoo authorization by getting the authorization URL from the backend
 */
async function handleWahooAuthorization() {
  try {
    wahooAuthStatus.value = null

    const authUrl = await getAuthUrl()

    // Redirect to Wahoo authorization URL
    window.location.href = authUrl
  } catch (error: any) {
    console.error('Wahoo authorization error:', error)
    wahooAuthStatus.value = {
      status: 'error',
      message: error.message || 'Failed to initiate Wahoo authorization',
      icon: 'fa-solid fa-exclamation-triangle'
    }
  }
}

// Check authorization on mount
onMounted(() => {
  // Use a watcher to handle authorization changes
  // This ensures we check authorization after it's been loaded
  let unwatch: (() => void) | null = null

  unwatch = watch(
    [isAuthorized, isLoadingAuthorization],
    ([authorized, loading]) => {
      // Only redirect if authorization check is complete and user is not authorized
      if (!loading && !authorized) {
        window.location.href = '/'
        if (unwatch) {
          unwatch() // Stop watching after redirect
        }
      }
    },
    { immediate: true }
  )
})
</script>

<style scoped>
.labs-page {
  min-height: calc(100vh - var(--navbar-height));
  padding: 2rem 1rem;
  background: var(--bg-secondary);
}

.labs-container {
  max-width: 800px;
  margin: 0 auto;
}

.labs-header {
  text-align: center;
  margin-bottom: 3rem;
}

.labs-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
}

.labs-title i {
  color: var(--brand-primary);
}

.labs-description {
  font-size: 1.125rem;
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.6;
}

.labs-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.labs-section {
  background: var(--bg-tertiary);
  border-radius: 12px;
  padding: 2rem;
  box-shadow: var(--card-shadow);
  border: 1px solid var(--border-color);
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-title i {
  color: var(--brand-primary);
}

.section-description {
  color: var(--text-secondary);
  margin: 0 0 1.5rem 0;
  line-height: 1.6;
}

.wahoo-auth-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.auth-status {
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 500;
}

.status-indicator.success {
  color: var(--success-color);
  background: var(--success-background);
  border-color: var(--success-border);
}

.status-indicator.error {
  color: var(--error-color);
  background: var(--error-background);
  border-color: var(--error-border);
}

.status-indicator.info {
  color: var(--info-color);
  background: var(--info-background);
  border-color: var(--info-border);
}

.wahoo-auth-btn {
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.wahoo-auth-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.info-content {
  color: var(--text-secondary);
  line-height: 1.6;
}

.info-list {
  margin: 1rem 0 0 0;
  padding-left: 1.5rem;
}

.info-list li {
  margin-bottom: 0.5rem;
}

/* Responsive design */
@media (max-width: 768px) {
  .labs-page {
    padding: 1rem 0.5rem;
  }

  .labs-title {
    font-size: 2rem;
  }

  .labs-section {
    padding: 1.5rem;
  }

  .wahoo-auth-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
