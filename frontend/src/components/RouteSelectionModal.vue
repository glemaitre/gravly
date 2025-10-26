<template>
  <div class="modal-overlay" @click="emit('close')">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3 class="modal-title">
          <i class="fa-solid fa-route"></i>
          {{ $t('labs.wahooIntegration.selectRoute') }}
        </h3>
        <button class="close-button" @click="emit('close')">
          <i class="fa-solid fa-times"></i>
        </button>
      </div>

      <div class="modal-body">
        <!-- Loading State -->
        <div v-if="isLoading" class="loading-state">
          <i class="fa-solid fa-circle-notch fa-spin"></i>
          <span>{{ $t('common.loading') }}</span>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="error-state">
          <i class="fa-solid fa-exclamation-triangle"></i>
          <span>{{ error }}</span>
          <button class="btn btn-secondary retry-button" @click="loadRoutes">
            <i class="fa-solid fa-sync"></i>
            {{ $t('common.retry') }}
          </button>
        </div>

        <!-- Empty State -->
        <div v-else-if="routes.length === 0" class="empty-state">
          <i class="fa-solid fa-inbox"></i>
          <span>{{ $t('labs.wahooIntegration.noRoutes') }}</span>
        </div>

        <!-- Routes List -->
        <div v-else class="routes-list">
          <div
            v-for="route in routes"
            :key="route.id"
            class="route-item"
            :class="{ selected: selectedRoute?.id === route.id }"
            @click="selectRoute(route)"
          >
            <div class="route-info">
              <div class="route-name">{{ route.name }}</div>
              <div class="route-details">
                <span class="route-distance">
                  <i class="fa-solid fa-route"></i>
                  {{ formatDistance(route.distance) }}
                </span>
                <span class="route-elevation">
                  <i class="fa-solid fa-mountain"></i>
                  {{ formatElevation(route.elevation_gain) }}
                </span>
              </div>
            </div>
            <div class="route-select">
              <i
                class="fa-solid"
                :class="selectedRoute?.id === route.id ? 'fa-check-circle' : 'fa-circle'"
              ></i>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button
          class="btn btn-secondary"
          @click="emit('close')"
        >
          {{ $t('common.cancel') }}
        </button>
        <button
          class="btn btn-primary"
          :disabled="!selectedRoute"
          @click="handleUpload"
        >
          <i class="fa-solid fa-cloud-upload-alt"></i>
          {{ $t('labs.wahooIntegration.uploadButton') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, onMounted } from 'vue'
import { useWahooApi } from '../composables/useWahooApi'

interface Route {
  id: string
  name: string
  distance: number
  elevation_gain: number
}

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'route-selected', route: Route): void
}>()

const { getRoutes, isLoading } = useWahooApi()
const routes = ref<Route[]>([])
const selectedRoute = ref<Route | null>(null)
const error = ref<string | null>(null)

/**
 * Load available routes
 */
async function loadRoutes() {
  try {
    error.value = null
    routes.value = await getRoutes()
  } catch (err: any) {
    console.error('Failed to load routes:', err)
    error.value = err.message || 'Failed to load routes'
  }
}

/**
 * Select a route
 */
function selectRoute(route: Route) {
  selectedRoute.value = route
}

/**
 * Handle route upload
 */
function handleUpload() {
  if (selectedRoute.value) {
    emit('route-selected', selectedRoute.value)
  }
}

/**
 * Format distance in kilometers
 */
function formatDistance(meters: number): string {
  const km = meters / 1000
  return `${km.toFixed(1)} km`
}

/**
 * Format elevation in meters
 */
function formatElevation(meters: number): string {
  return `${Math.round(meters)} m`
}

// Load routes when component mounts
onMounted(() => {
  loadRoutes()
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-tertiary);
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--modal-shadow);
  border: 1px solid var(--border-color);
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-title {
  margin: 0;
  font-size: 1.25rem;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.modal-title i {
  color: var(--brand-primary);
}

.close-button {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.5rem;
  font-size: 1.25rem;
  transition: color 0.2s;
}

.close-button:hover {
  color: var(--text-primary);
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
  min-height: 200px;
}

.loading-state,
.error-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  height: 200px;
  color: var(--text-secondary);
}

.loading-state i,
.error-state i,
.empty-state i {
  font-size: 2rem;
  color: var(--text-secondary);
}

.retry-button {
  margin-top: 1rem;
}

.routes-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.route-item {
  padding: 1rem;
  border-radius: 8px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
}

.route-item:hover {
  border-color: var(--brand-primary);
  background: var(--bg-hover);
}

.route-item.selected {
  border-color: var(--brand-primary);
  background: var(--brand-background);
}

.route-info {
  flex: 1;
}

.route-name {
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 0.25rem;
}

.route-details {
  display: flex;
  gap: 1rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.route-distance,
.route-elevation {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.route-select {
  color: var(--brand-primary);
  font-size: 1.25rem;
  width: 2rem;
  display: flex;
  justify-content: center;
}

.modal-footer {
  padding: 1.5rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    max-height: 95vh;
  }

  .modal-header {
    padding: 1rem;
  }

  .modal-body {
    padding: 1rem;
  }

  .modal-footer {
    padding: 1rem;
  }

  .route-item {
    padding: 0.75rem;
  }
}
</style>
