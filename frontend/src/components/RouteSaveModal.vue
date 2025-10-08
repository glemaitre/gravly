<template>
  <div class="route-save-section">
    <button
      class="save-route-btn"
      :class="{ disabled: isDisabled }"
      :disabled="isDisabled"
      @click="handleSaveRoute"
      :title="disabledTitle"
    >
      <i class="fa-solid fa-save"></i>
      <span>{{ t('routePlanner.saveRoute') }}</span>
    </button>

    <!-- Save Route Modal -->
    <div v-if="isModalVisible" class="modal-overlay" @click="closeSaveModal">
      <div class="modal-content" @click.stop>
        <div class="header">
          <h3 class="modal-title">
            <i class="fa-solid fa-floppy-disk"></i>
            {{ t('routePlanner.saveRouteTitle') }}
          </h3>
          <button class="modal-close" @click="closeSaveModal">
            <i class="fa-solid fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label for="route-name">{{ t('routePlanner.routeName') }}</label>
            <input
              id="route-name"
              v-model="routeName"
              type="text"
              :placeholder="t('routePlanner.routeNamePlaceholder')"
              class="form-input"
              maxlength="100"
            />
          </div>

          <div class="form-group">
            <label>{{ t('routePlanner.routeStats') }}</label>
            <RouteInfoCard
              :stats="computedStats"
              :has-segment-data="props.selectedSegments.length > 0"
            />
          </div>

          <div class="form-group">
            <label for="route-comments">{{ t('routePlanner.routeComments') }}</label>
            <textarea
              id="route-comments"
              v-model="routeComments"
              :placeholder="t('routePlanner.routeCommentsPlaceholder')"
              class="form-textarea"
              rows="3"
              maxlength="500"
            ></textarea>
          </div>
        </div>

        <div class="modal-footer">
          <button
            class="btn-primary"
            @click="confirmSaveRoute"
            :disabled="!routeName.trim() || isSaving"
          >
            <i v-if="isSaving" class="fa-solid fa-spinner fa-spin"></i>
            <span>{{ isSaving ? t('common.saving') : t('common.save') }}</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Success/Error Messages -->
    <div v-if="showSuccessMessage" class="save-success-message">
      <i class="fa-solid fa-check-circle"></i>
      <span>{{ t('routePlanner.routeSavedSuccessfully') }}</span>
    </div>

    <div v-if="showErrorMessage" class="save-error-message">
      <i class="fa-solid fa-exclamation-circle"></i>
      <span>{{ errorMessage }}</span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { TrackResponse, SurfaceType } from '../types'
import RouteInfoCard from './RouteInfoCard.vue'

interface RouteStats {
  distance: number // in kilometers
  difficulty: number // average difficulty (1-5)
  elevationGain: number // in meters
  elevationLoss: number // in meters
  surfaceTypes: SurfaceType[]
  tireDry: 'slick' | 'semi-slick' | 'knobs'
  tireWet: 'slick' | 'semi-slick' | 'knobs'
}

interface Props {
  selectedSegments: TrackResponse[]
  routeDistance: number
  elevationStats: {
    totalGain: number
    totalLoss: number
    maxElevation: number
    minElevation: number
  }
  routeTrackPoints: Array<{
    lat: number
    lng: number
    elevation: number
    distance: number
  }>
  show?: boolean
}

interface Emits {
  // eslint-disable-next-line no-unused-vars
  (event: 'route-saved', routeId: number): void
  // eslint-disable-next-line no-unused-vars
  (event: 'close'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
const { t } = useI18n()

// Component state
const showSaveModal = ref(false)
const routeName = ref('')
const routeComments = ref('')
const isSaving = ref(false)
const showSuccessMessage = ref(false)
const showErrorMessage = ref(false)
const errorMessage = ref('')

// Modal visibility - use external prop if provided, otherwise use internal state
const isModalVisible = computed(() => {
  return props.show !== undefined ? props.show : showSaveModal.value
})

// Computed properties
const isDisabled = computed(() => {
  return props.selectedSegments.length === 0 || !props.routeDistance
})

const disabledTitle = computed(() => {
  if (props.selectedSegments.length === 0) {
    return t('routePlanner.noSegmentsSelected')
  }
  if (!props.routeDistance) {
    return t('routePlanner.noRouteDistance')
  }
  return ''
})

const computedStats = computed((): RouteStats => {
  if (props.selectedSegments.length === 0) {
    // For waypoint routes (no segments), show basic route info
    return {
      distance: props.routeDistance,
      difficulty: 0, // No difficulty for waypoint routes
      elevationGain: props.elevationStats.totalGain,
      elevationLoss: props.elevationStats.totalLoss,
      surfaceTypes: [], // No surface data for waypoint routes
      tireDry: 'slick', // Default recommendation
      tireWet: 'slick' // Default recommendation
    }
  }

  // Calculate average difficulty
  const totalDifficulty = props.selectedSegments.reduce((sum, segment) => {
    return sum + segment.difficulty_level
  }, 0)
  const averageDifficulty = totalDifficulty / props.selectedSegments.length

  // Union of all surface types
  const allSurfaceTypes = new Set<SurfaceType>()
  props.selectedSegments.forEach((segment) => {
    segment.surface_type.forEach((surface) => {
      allSurfaceTypes.add(surface as SurfaceType)
    })
  })

  // Tire recommendation logic: worst case scenario
  // Order: slick < semi-slick < knobs (from best to worst)
  let tireDry: 'slick' | 'semi-slick' | 'knobs' = 'slick'
  let tireWet: 'slick' | 'semi-slick' | 'knobs' = 'slick'

  // Calculate dry tire recommendation
  const allDryTireTypes = new Set<string>()
  props.selectedSegments.forEach((segment) => {
    allDryTireTypes.add(segment.tire_dry)
  })

  if (allDryTireTypes.has('knobs')) {
    tireDry = 'knobs'
  } else if (allDryTireTypes.has('semi-slick')) {
    tireDry = 'semi-slick'
  }

  // Calculate wet tire recommendation
  const allWetTireTypes = new Set<string>()
  props.selectedSegments.forEach((segment) => {
    allWetTireTypes.add(segment.tire_wet)
  })

  if (allWetTireTypes.has('knobs')) {
    tireWet = 'knobs'
  } else if (allWetTireTypes.has('semi-slick')) {
    tireWet = 'semi-slick'
  }

  return {
    distance: props.routeDistance,
    difficulty: averageDifficulty,
    elevationGain: props.elevationStats.totalGain,
    elevationLoss: props.elevationStats.totalLoss,
    surfaceTypes: Array.from(allSurfaceTypes),
    tireDry,
    tireWet
  }
})

// Methods
function handleSaveRoute() {
  if (isDisabled.value) return

  showSaveModal.value = true
  showSuccessMessage.value = false
  showErrorMessage.value = false
}

function closeSaveModal() {
  showSaveModal.value = false
  routeName.value = ''
  routeComments.value = ''
  showErrorMessage.value = false
  errorMessage.value = ''
  emit('close')
}

async function confirmSaveRoute() {
  if (!routeName.value.trim()) return

  isSaving.value = true
  showErrorMessage.value = false
  errorMessage.value = ''

  try {
    // Create the route data
    const routeData = {
      name: routeName.value.trim(),
      track_type: 'route',
      segments: props.selectedSegments.map((segment) => ({
        id: segment.id,
        isReversed: segment.isReversed || false
      })),
      computed_stats: computedStats.value,
      route_track_points: props.routeTrackPoints,
      comments: routeComments.value.trim()
    }

    // Call the backend API to save the route
    const response = await fetch('/api/routes/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(routeData)
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(error || 'Failed to save route')
    }

    const result = await response.json()

    // Show success message
    showSuccessMessage.value = true
    showSaveModal.value = false

    // Emit event to parent component
    emit('route-saved', result.id)

    // Hide success message after 3 seconds
    setTimeout(() => {
      showSuccessMessage.value = false
    }, 3000)
  } catch (error: any) {
    showErrorMessage.value = true
    errorMessage.value = error.message || t('routePlanner.saveRouteError')

    // Hide error message after 5 seconds
    setTimeout(() => {
      showErrorMessage.value = false
      errorMessage.value = ''
    }, 5000)
  } finally {
    isSaving.value = false
  }
}
</script>

<style scoped>
.route-save-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.save-route-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: var(--brand-500, #ff6600);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.save-route-btn:hover:not(.disabled) {
  background: var(--brand-600, #e65c00);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(255, 102, 0, 0.3);
}

.save-route-btn:active:not(.disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 4px rgba(255, 102, 0, 0.3);
}

.save-route-btn.disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.save-route-btn i {
  font-size: 0.875rem;
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.modal-content {
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
  max-width: 550px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.header h3,
.modal-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
}

.modal-title i {
  color: var(--brand-500, #ff6600);
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: #f3f4f6;
  color: #6b7280;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #e5e7eb;
  color: #374151;
}

.modal-body {
  padding: 1.5rem;
  flex: 1;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-input,
.form-textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  transition: border-color 0.2s ease;
  box-sizing: border-box;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--brand-500, #ff6600);
  box-shadow: 0 0 0 3px rgba(255, 102, 0, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
  justify-content: flex-end;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: none;
  background: var(--brand-500, #ff6600);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--brand-600, #e65c00);
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

/* Success/Error Messages */
.save-success-message,
.save-error-message {
  position: fixed;
  top: 2rem;
  right: 2rem;
  padding: 1rem 1.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  z-index: 1001;
  max-width: 400px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.save-success-message {
  background: #f0fdf4;
  color: #15803d;
  border: 1px solid #bbf7d0;
}

.save-error-message {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

@media (max-width: 640px) {
  .modal-content {
    margin: 1rem;
    max-width: calc(100vw - 2rem);
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 1rem;
  }

  .save-success-message,
  .save-error-message {
    right: 1rem;
    left: 1rem;
    max-width: none;
  }
}
</style>
