<template>
  <div class="labs-page">
    <div class="page">
      <div class="main-col">
        <div class="card">
          <div class="card-header">
            <h1 class="card-title">
              <i class="fa-solid fa-flask"></i>
              {{ $t('labs.title') }}
            </h1>
            <p class="card-subtitle">{{ $t('labs.subtitle') }}</p>
          </div>

          <div class="card-content">
            <!-- Wahoo Cloud API Integration -->
            <div class="experiment-section">
              <h2 class="experiment-title">
                <i class="fa-solid fa-cloud"></i>
                {{ $t('labs.wahoo.title') }}
              </h2>
              <p class="experiment-description">
                {{ $t('labs.wahoo.description') }}
              </p>

              <div class="wahoo-status">
                <div v-if="wahooLoading" class="status-loading">
                  <i class="fa-solid fa-spinner fa-spin"></i>
                  {{ $t('labs.wahoo.checkingStatus') }}
                </div>

                <div v-else-if="wahooConnected" class="status-connected">
                  <i class="fa-solid fa-check-circle"></i>
                  {{ $t('labs.wahoo.connected') }}
                  <div class="user-info">
                    <strong
                      >{{ wahooUser?.firstname }} {{ wahooUser?.lastname }}</strong
                    >
                    <span class="user-id">ID: {{ wahooUser?.id }}</span>
                  </div>
                </div>

                <div v-else class="status-disconnected">
                  <i class="fa-solid fa-exclamation-circle"></i>
                  {{ $t('labs.wahoo.notConnected') }}
                </div>
              </div>

              <div class="wahoo-actions">
                <button
                  v-if="!wahooConnected"
                  @click="connectWahoo"
                  :disabled="wahooLoading"
                  class="btn btn-primary"
                >
                  <i class="fa-solid fa-link"></i>
                  {{ $t('labs.wahoo.connect') }}
                </button>

                <button
                  v-else
                  @click="disconnectWahoo"
                  :disabled="wahooLoading"
                  class="btn btn-secondary"
                >
                  <i class="fa-solid fa-unlink"></i>
                  {{ $t('labs.wahoo.disconnect') }}
                </button>

                <button
                  v-if="wahooConnected"
                  @click="testWahooApi"
                  :disabled="wahooLoading"
                  class="btn btn-outline"
                >
                  <i class="fa-solid fa-vial"></i>
                  {{ $t('labs.wahoo.testApi') }}
                </button>
              </div>

              <!-- API Test Results -->
              <div v-if="wahooTestResults" class="test-results">
                <h3>{{ $t('labs.wahoo.testResults') }}</h3>
                <pre class="test-output">{{ wahooTestResults }}</pre>
              </div>
            </div>

            <!-- Future Experiments Placeholder -->
            <div class="experiment-section">
              <h2 class="experiment-title">
                <i class="fa-solid fa-plus"></i>
                {{ $t('labs.future.title') }}
              </h2>
              <p class="experiment-description">
                {{ $t('labs.future.description') }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Messages -->
    <p v-if="message" class="message">{{ message }}</p>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'

// Wahoo API state
const wahooLoading = ref(false)
const wahooConnected = ref(false)
const wahooUser = ref<{
  id: number
  firstname: string
  lastname: string
} | null>(null)
const wahooTestResults = ref<string | null>(null)
const message = ref('')

onMounted(async () => {
  await checkWahooStatus()
})

/**
 * Check if user is connected to Wahoo API
 */
async function checkWahooStatus(): Promise<void> {
  try {
    wahooLoading.value = true
    const response = await fetch('/api/wahoo/status', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      wahooConnected.value = data.connected
      wahooUser.value = data.user
    } else {
      wahooConnected.value = false
      wahooUser.value = null
    }
  } catch (error) {
    console.error('Failed to check Wahoo status:', error)
    wahooConnected.value = false
    wahooUser.value = null
  } finally {
    wahooLoading.value = false
  }
}

/**
 * Initiate Wahoo OAuth2 connection
 */
async function connectWahoo(): Promise<void> {
  try {
    wahooLoading.value = true
    const response = await fetch('/api/wahoo/authorize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const data = await response.json()
      // Redirect to Wahoo authorization URL
      window.location.href = data.authorization_url
    } else {
      const errorData = await response.json()
      message.value = errorData.detail || 'Failed to initiate Wahoo connection'
    }
  } catch (error) {
    console.error('Failed to connect to Wahoo:', error)
    message.value = 'Failed to connect to Wahoo API'
  } finally {
    wahooLoading.value = false
  }
}

/**
 * Disconnect from Wahoo API
 */
async function disconnectWahoo(): Promise<void> {
  try {
    wahooLoading.value = true
    const response = await fetch('/api/wahoo/disconnect', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      wahooConnected.value = false
      wahooUser.value = null
      wahooTestResults.value = null
      message.value = 'Disconnected from Wahoo API'
    } else {
      const errorData = await response.json()
      message.value = errorData.detail || 'Failed to disconnect from Wahoo'
    }
  } catch (error) {
    console.error('Failed to disconnect from Wahoo:', error)
    message.value = 'Failed to disconnect from Wahoo API'
  } finally {
    wahooLoading.value = false
  }
}

/**
 * Test Wahoo API connection
 */
async function testWahooApi(): Promise<void> {
  try {
    wahooLoading.value = true
    wahooTestResults.value = null

    const response = await fetch('/api/wahoo/test', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    const data = await response.json()

    if (response.ok) {
      wahooTestResults.value = JSON.stringify(data, null, 2)
      message.value = 'Wahoo API test completed successfully'
    } else {
      wahooTestResults.value = `Error: ${data.detail || 'Unknown error'}`
      message.value = 'Wahoo API test failed'
    }
  } catch (error) {
    console.error('Failed to test Wahoo API:', error)
    wahooTestResults.value = `Error: ${error}`
    message.value = 'Failed to test Wahoo API'
  } finally {
    wahooLoading.value = false
  }
}
</script>

<style scoped>
.labs-page {
  padding-top: var(--navbar-height);
  min-height: 100vh;
  background: var(--bg-secondary);
}

.page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.main-col {
  width: 100%;
}

.card {
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 12px;
  box-shadow: var(--card-shadow);
  overflow: hidden;
}

.card-header {
  padding: 2rem 2rem 1rem;
  border-bottom: 1px solid var(--border-primary);
}

.card-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.card-subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin: 0;
}

.card-content {
  padding: 2rem;
}

.experiment-section {
  margin-bottom: 3rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--border-primary);
}

.experiment-section:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.experiment-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 1rem 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.experiment-description {
  font-size: 1rem;
  color: var(--text-secondary);
  margin: 0 0 1.5rem 0;
  line-height: 1.6;
}

.wahoo-status {
  margin-bottom: 1.5rem;
  padding: 1rem;
  border-radius: 8px;
  background: var(--bg-tertiary);
}

.status-loading {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.status-connected {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #059669;
  font-weight: 500;
}

.status-disconnected {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #dc2626;
  font-weight: 500;
}

.user-info {
  margin-left: 1rem;
  font-size: 0.9rem;
  color: var(--text-secondary);
}

.user-id {
  margin-left: 0.5rem;
  font-family: monospace;
  background: var(--bg-primary);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.8rem;
}

.wahoo-actions {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.95rem;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--brand-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--brand-primary-hover);
}

.btn-secondary {
  background: var(--text-secondary);
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: var(--text-primary);
}

.btn-outline {
  background: transparent;
  color: var(--brand-primary);
  border: 2px solid var(--brand-primary);
}

.btn-outline:hover:not(:disabled) {
  background: var(--brand-primary);
  color: white;
}

.test-results {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--bg-tertiary);
  border-radius: 8px;
  border: 1px solid var(--border-primary);
}

.test-results h3 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
  color: var(--text-primary);
}

.test-output {
  background: var(--bg-primary);
  border: 1px solid var(--border-secondary);
  border-radius: 4px;
  padding: 1rem;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.85rem;
  color: var(--text-primary);
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.message {
  position: fixed;
  top: calc(var(--navbar-height) + 1rem);
  right: 1rem;
  background: var(--brand-primary);
  color: white;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  box-shadow: var(--shadow-lg);
  z-index: 1000;
  max-width: 400px;
  word-wrap: break-word;
}

@media (max-width: 768px) {
  .page {
    padding: 1rem;
  }

  .card-header,
  .card-content {
    padding: 1.5rem;
  }

  .wahoo-actions {
    flex-direction: column;
  }

  .btn {
    justify-content: center;
  }
}
</style>
