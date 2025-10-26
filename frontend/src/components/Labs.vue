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
            <!-- Authentication Status -->
            <div class="auth-status">
              <div 
                v-if="isWahooAuthenticated" 
                class="status-indicator success"
              >
                <i class="fa-solid fa-check-circle"></i>
                <span>{{ $t('labs.wahooIntegration.connected') }}</span>
                <span class="token-expiry" v-if="tokenExpiresIn">
                  ({{ Math.floor(tokenExpiresIn / 60) }}m {{ tokenExpiresIn % 60 }}s)
                </span>
              </div>
              <div 
                v-else-if="wahooAuthStatus" 
                class="status-indicator"
                :class="wahooAuthStatus.status"
              >
                <i :class="wahooAuthStatus.icon"></i>
                <span>{{ wahooAuthStatus.message }}</span>
              </div>
              <div 
                v-else 
                class="status-indicator info"
              >
                <i class="fa-solid fa-info-circle"></i>
                <span>{{ $t('labs.wahooIntegration.notConnected') }}</span>
              </div>
            </div>

            <!-- Authentication Button -->
            <button
              class="btn btn-primary wahoo-auth-btn"
              @click="handleWahooAuthorization"
              :disabled="isLoadingWahooAuth"
            >
              <i class="fa-solid" :class="isWahooAuthenticated ? 'fa-sync' : 'fa-external-link-alt'"></i>
              <span v-if="!isLoadingWahooAuth">
                {{ isWahooAuthenticated 
                  ? $t('labs.wahooIntegration.refreshButton')
                  : $t('labs.wahooIntegration.authorizeButton')
                }}
              </span>
              <span v-else>{{ $t('labs.wahooIntegration.authorizing') }}</span>
            </button>

            <!-- Route Upload Section (only shown when authenticated) -->
            <div v-if="isWahooAuthenticated" class="route-upload-section">
              <button
                class="btn btn-secondary upload-route-btn"
                @click="showRouteModal = true"
                :disabled="isLoadingWahooAuth"
              >
                <i class="fa-solid fa-cloud-upload-alt"></i>
                <span>{{ $t('labs.wahooIntegration.uploadRouteButton') }}</span>
              </button>
            </div>
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

        <!-- Route Selection Modal -->
        <RouteSelectionModal
          v-if="showRouteModal"
          @close="showRouteModal = false"
          @route-selected="handleRouteSelected"
        />
      </section>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useAuthorization } from '../composables/useAuthorization'
import { useWahooApi } from '../composables/useWahooApi'
import RouteSelectionModal from './RouteSelectionModal.vue'

// Authorization check
const { isAuthorized, isLoadingAuthorization } = useAuthorization()

// Wahoo API composable
const { 
  getAuthUrl, 
  isLoading: isLoadingWahooAuth,
  authState,
  attemptTokenRefresh,
  clearAuth,
  uploadRoute
} = useWahooApi()

// Computed properties for auth status
const isWahooAuthenticated = computed(() => authState.value.isAuthenticated)
const tokenExpiresIn = computed(() => {
  if (!authState.value.expiresAt) return null
  const now = Date.now()
  const expiresAt = authState.value.expiresAt * 1000
  return Math.max(0, Math.floor((expiresAt - now) / 1000))
})

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

    if (isWahooAuthenticated.value) {
      // If authenticated, try to refresh token
      const refreshed = await attemptTokenRefresh()
      if (refreshed) {
        wahooAuthStatus.value = {
          status: 'success',
          message: 'Token refreshed successfully',
          icon: 'fa-solid fa-check-circle'
        }
        return
      }
      // If refresh failed, clear auth and proceed with new authorization
      clearAuth()
    }

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

/**
 * Handle token refresh
 */
async function handleTokenRefresh() {
  try {
    wahooAuthStatus.value = {
      status: 'info',
      message: 'Refreshing token...',
      icon: 'fa-solid fa-sync fa-spin'
    }

    const refreshed = await attemptTokenRefresh()
    
    if (refreshed) {
      wahooAuthStatus.value = {
        status: 'success',
        message: 'Token refreshed successfully',
        icon: 'fa-solid fa-check-circle'
      }
    } else {
      throw new Error('Token refresh failed')
    }
  } catch (error: any) {
    console.error('Token refresh error:', error)
    wahooAuthStatus.value = {
      status: 'error',
      message: 'Failed to refresh token',
      icon: 'fa-solid fa-exclamation-triangle'
    }
    clearAuth()
  }
}

// Watch token expiration and refresh when needed
watch(tokenExpiresIn, (seconds) => {
  if (seconds && seconds < 300 && seconds > 0) { // Refresh when less than 5 minutes remain
    handleTokenRefresh()
  }
})

// Route selection modal state
const showRouteModal = ref(false)

/**
 * Handle route selection from modal
 */
async function handleRouteSelected(route: any) {
  try {
    wahooAuthStatus.value = {
      status: 'info',
      message: 'Uploading route to Wahoo...',
      icon: 'fa-solid fa-sync fa-spin'
    }

    await uploadRoute(route.id)

    wahooAuthStatus.value = {
      status: 'success',
      message: 'Route uploaded successfully',
      icon: 'fa-solid fa-check-circle'
    }

    showRouteModal.value = false
  } catch (error: any) {
    console.error('Route upload error:', error)
    wahooAuthStatus.value = {
      status: 'error',
      message: error.message || 'Failed to upload route',
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

.wahoo-auth-btn,
.upload-route-btn {
  align-self: flex-start;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  border-radius: 8px;
  transition: all 0.2s ease;
  width: 100%;
  justify-content: center;
}

.wahoo-auth-btn:disabled,
.upload-route-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.route-upload-section {
  margin-top: 1rem;
  width: 100%;
}

.token-expiry {
  font-size: 0.875rem;
  opacity: 0.8;
  margin-left: 0.5rem;
}

.info-content {
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Status indicator improvements */
.status-indicator {
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.status-indicator i {
  font-size: 1rem;
}

.status-indicator.success {
  background-color: var(--success-background);
  color: var(--success-color);
  border: 1px solid var(--success-border);
}

.status-indicator.error {
  background-color: var(--error-background);
  color: var(--error-color);
  border: 1px solid var(--error-border);
}

.status-indicator.info {
  background-color: var(--info-background);
  color: var(--info-color);
  border: 1px solid var(--info-border);
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

  .wahoo-auth-btn,
  .upload-route-btn {
    width: 100%;
    justify-content: center;
  }

  .status-indicator {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 1rem;
  }

  .token-expiry {
    margin-left: 0;
    margin-top: 0.25rem;
  }

  .route-upload-section {
    margin-top: 1.5rem;
  }
}

@media (max-width: 480px) {
  .labs-title {
    font-size: 1.75rem;
  }

  .section-title {
    font-size: 1.25rem;
  }

  .labs-description {
    font-size: 1rem;
  }

  .status-indicator {
    font-size: 0.875rem;
  }

  .token-expiry {
    font-size: 0.75rem;
  }
}
</style>
