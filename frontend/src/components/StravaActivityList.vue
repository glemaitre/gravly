<template>
  <div class="strava-activity-list">
    <div class="header">
      <h3>{{ t('strava.activities') }}</h3>
      <div class="header-actions">
        <button
          @click="refreshActivities"
          :disabled="isLoading"
          class="btn btn-secondary btn-sm"
          :title="t('strava.refresh')"
        >
          <i class="fa-solid fa-refresh" :class="{ 'fa-spin': isLoading }"></i>
        </button>
        <button
          @click="$emit('close')"
          class="btn btn-secondary btn-sm"
          :title="t('common.close')"
        >
          <i class="fa-solid fa-times"></i>
        </button>
      </div>
    </div>

    <div v-if="error" class="error-message">
      <i class="fa-solid fa-exclamation-triangle" style="color: #f97316"></i>
      {{ error }}
    </div>

    <div v-if="isLoading && activities.length === 0" class="loading">
      <i class="fa-solid fa-spinner fa-spin" style="color: #f97316"></i>
      {{ t('strava.loadingActivities') }}
    </div>

    <div v-else-if="activities.length === 0" class="empty-state">
      <i class="fa-solid fa-bicycle" style="color: #f97316"></i>
      <p>{{ t('strava.noActivities') }}</p>
    </div>

    <div v-else class="activities-container">
      <div
        v-for="activity in activities"
        :key="activity.id"
        class="activity-card"
        :class="{ selected: selectedActivityId === activity.id }"
        @click="selectActivity(activity)"
      >
        <div class="activity-preview">
          <div class="activity-info">
            <h4 class="activity-name">{{ activity.name }}</h4>
            <div class="activity-stats">
              <div class="stat">
                <i class="fa-solid fa-route" style="color: #f97316"></i>
                <span>{{ formatDistance(activity.distance) }}</span>
              </div>
              <div class="stat">
                <i class="fa-solid fa-clock" style="color: #f97316"></i>
                <span>{{ formatDuration(activity.moving_time) }}</span>
              </div>
              <div class="stat">
                <i class="fa-solid fa-mountain" style="color: #f97316"></i>
                <span>{{ formatElevation(activity.total_elevation_gain) }}</span>
              </div>
            </div>
            <div class="activity-meta">
              <span class="activity-date">
                <i
                  class="fa-solid fa-calendar"
                  style="color: #f97316; margin-right: 0.25rem"
                ></i>
                {{ formatDate(activity.start_date_local) }}
              </span>
              <div class="activity-type-badge">
                <span class="activity-type">{{ activity.type }}</span>
                <span
                  v-if="activity.start_latlng"
                  class="gps-indicator"
                  title="GPS data available"
                >
                  <i class="fa-solid fa-location-dot" style="color: #f97316"></i>
                </span>
              </div>
            </div>
          </div>
          <div class="activity-map">
            <div ref="mapContainer" :id="`map-${activity.id}`" class="mini-map"></div>
            <div v-if="!activity.start_latlng" class="no-gps-warning">
              <i class="fa-solid fa-exclamation-triangle" style="color: #f97316"></i>
              <span>{{ t('strava.noGpsData') }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="hasMore" class="load-more">
        <button
          @click="() => loadMoreActivities()"
          :disabled="isLoading"
          class="btn btn-load-more"
        >
          <i v-if="isLoading" class="fa-solid fa-spinner fa-spin"></i>
          <i v-else class="fa-solid fa-plus"></i>
          {{ t('strava.loadMore') }}
        </button>
      </div>
    </div>

    <!-- Activity Details Modal -->
    <StravaActivityDetailsModal
      :is-visible="showDetailsModal"
      :activity="selectedActivity"
      :is-importing="isImporting"
      @close="showDetailsModal = false"
      @import="importActivity"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import { useStravaActivities } from '../composables/useStravaActivities'
import type { StravaActivity } from '../composables/useStravaApi'
import StravaActivityDetailsModal from './StravaActivityDetailsModal.vue'

const { t, locale } = useI18n()
const {
  activities,
  isLoading,
  error,
  hasMore,
  loadActivities,
  loadMoreActivities,
  refreshActivities,
  getActivityGpx
} = useStravaActivities()

const emit = defineEmits<{
  close: []
  import: [gpxData: any]
}>()

const selectedActivityId = ref<string | null>(null)
const selectedActivity = ref<StravaActivity | null>(null)
const isImporting = ref(false)
const showDetailsModal = ref(false)
const mapContainer = ref<HTMLElement[]>([])
const maps = ref<globalThis.Map<string, any>>(new globalThis.Map())

const selectActivity = (activity: StravaActivity) => {
  selectedActivityId.value = activity.id
  selectedActivity.value = activity
  showDetailsModal.value = true
}

const importActivity = async (activity: StravaActivity) => {
  try {
    console.log(
      `🚀 StravaActivityList: Starting import for activity ${activity.id} (${activity.name})`
    )
    isImporting.value = true
    const gpxData = await getActivityGpx(activity.id)
    console.log(
      `✅ StravaActivityList: GPX data received:`,
      gpxData ? 'Success' : 'Failed'
    )

    if (gpxData) {
      emit('import', gpxData)
    }
  } catch (err) {
    console.error('Failed to import activity:', err)
  } finally {
    isImporting.value = false
  }
}

const createMiniMap = async (activity: StravaActivity, containerId: string) => {
  await nextTick()

  const container = document.getElementById(containerId)
  if (!container) return

  // Don't create map if it already exists
  if (maps.value.has(activity.id)) return

  try {
    const map = L.map(container, {
      zoomControl: false,
      attributionControl: false,
      dragging: false,
      touchZoom: false,
      doubleClickZoom: false,
      scrollWheelZoom: false,
      boxZoom: false,
      keyboard: false
    })

    const apiKey = import.meta.env.THUNDERFOREST_API_KEY || 'demo'
    L.tileLayer(`https://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=${apiKey}`, {
      attribution: 'Maps © <a href="https://www.thunderforest.com/">Thunderforest</a>, Data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map)

    // Create polyline from summary polyline if available
    if (activity.map && activity.map.summary_polyline) {
      try {
        // Decode the polyline to get coordinates
        const coordinates = decodePolyline(activity.map.summary_polyline)

        if (coordinates.length > 0) {
          // Subsample coordinates for better performance on mini maps
          const subsampledCoords = subsampleCoordinates(coordinates, 50) // Max 50 points

          // Create polyline
          const polyline = L.polyline(subsampledCoords, {
            color: '#f97316',
            weight: 3,
            opacity: 0.8
          }).addTo(map)

          // Fit map to polyline bounds
          map.fitBounds(polyline.getBounds(), { padding: [8, 8] })

          // Add start marker
          if (coordinates.length > 0) {
            L.circleMarker(coordinates[0], {
              radius: 4,
              fillColor: '#10b981',
              color: '#ffffff',
              weight: 2,
              opacity: 1,
              fillOpacity: 0.8
            }).addTo(map)
          }

          // Add end marker
          if (coordinates.length > 1) {
            L.circleMarker(coordinates[coordinates.length - 1], {
              radius: 4,
              fillColor: '#ef4444',
              color: '#ffffff',
              weight: 2,
              opacity: 1,
              fillOpacity: 0.8
            }).addTo(map)
          }
        }
      } catch (err) {
        console.warn('Failed to decode activity polyline:', err)
        // Fallback to start/end coordinates
        if (activity.start_latlng && activity.end_latlng) {
          const bounds = L.latLngBounds(activity.start_latlng, activity.end_latlng)
          map.fitBounds(bounds, { padding: [5, 5] })
        } else if (activity.start_latlng) {
          map.setView(activity.start_latlng, 10)
        }
      }
    } else if (activity.start_latlng && activity.end_latlng) {
      // Fallback: just show start and end points
      const bounds = L.latLngBounds(activity.start_latlng, activity.end_latlng)
      map.fitBounds(bounds, { padding: [5, 5] })

      L.marker(activity.start_latlng).addTo(map)
      L.marker(activity.end_latlng).addTo(map)
    } else if (activity.start_latlng) {
      map.setView(activity.start_latlng, 10)
      L.marker(activity.start_latlng).addTo(map)
    }

    maps.value.set(activity.id, map)
  } catch (err) {
    console.error('Failed to create mini map:', err)
  }
}

const destroyMaps = () => {
  maps.value.forEach((map) => {
    map.remove()
  })
  maps.value.clear()
}

// Helper functions for activity display
const formatDistance = (meters: number): string => {
  if (meters >= 1000) {
    return `${(meters / 1000).toFixed(1)} km`
  }
  return `${meters.toFixed(0)} m`
}

const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)

  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

const formatElevation = (meters: number): string => {
  return `${meters.toFixed(0)} m`
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  const currentLocale = locale.value === 'fr' ? 'fr-FR' : 'en-US'
  return date.toLocaleDateString(currentLocale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

// Decode Google Polyline encoded string to coordinates
const decodePolyline = (encoded: string): [number, number][] => {
  const coordinates: [number, number][] = []
  let index = 0
  const len = encoded.length
  let lat = 0
  let lng = 0

  while (index < len) {
    let b: number
    let shift = 0
    let result = 0
    do {
      b = encoded.charCodeAt(index++) - 63
      result |= (b & 0x1f) << shift
      shift += 5
    } while (b >= 0x20)
    const dlat = (result & 1) !== 0 ? ~(result >> 1) : result >> 1
    lat += dlat

    shift = 0
    result = 0
    do {
      b = encoded.charCodeAt(index++) - 63
      result |= (b & 0x1f) << shift
      shift += 5
    } while (b >= 0x20)
    const dlng = (result & 1) !== 0 ? ~(result >> 1) : result >> 1
    lng += dlng

    coordinates.push([lat / 1e5, lng / 1e5])
  }

  return coordinates
}

// Subsample coordinates to reduce the number of points for better performance
const subsampleCoordinates = (
  coordinates: [number, number][],
  maxPoints: number
): [number, number][] => {
  if (coordinates.length <= maxPoints) {
    return coordinates
  }

  const step = Math.ceil(coordinates.length / maxPoints)
  const subsampled: [number, number][] = []

  // Always include the first point
  subsampled.push(coordinates[0])

  // Sample points at regular intervals
  for (let i = step; i < coordinates.length - 1; i += step) {
    subsampled.push(coordinates[i])
  }

  // Always include the last point
  if (coordinates.length > 1) {
    subsampled.push(coordinates[coordinates.length - 1])
  }

  return subsampled
}

onMounted(async () => {
  await loadActivities()

  // Create mini maps after activities are loaded
  await nextTick()
  activities.value.forEach((activity) => {
    if (activity && activity.id) {
      createMiniMap(activity, `map-${activity.id}`)
    }
  })
})

// Watch for new activities and create minimaps for them
watch(
  activities,
  async (newActivities, oldActivities) => {
    if (newActivities && newActivities.length > (oldActivities?.length || 0)) {
      await nextTick()
      // Create minimaps for newly added activities
      const newlyAddedActivities = newActivities.slice(oldActivities?.length || 0)

      // Use a more reliable approach with retry logic
      const createMapsWithRetry = (retries = 3) => {
        newlyAddedActivities.forEach((activity) => {
          if (activity && activity.id) {
            const containerId = `map-${activity.id}`
            const container = document.getElementById(containerId)

            if (container) {
              // Container exists, create the map
              createMiniMap(activity, containerId)
            } else if (retries > 0) {
              // Container doesn't exist yet, retry after a short delay
              setTimeout(() => createMapsWithRetry(retries - 1), 50)
            }
          }
        })
      }

      createMapsWithRetry()
    }
  },
  { deep: true }
)

onUnmounted(() => {
  destroyMaps()
})

// Expose functions for testing
defineExpose({
  formatDate,
  formatDistance,
  formatDuration,
  formatElevation
})
</script>

<style scoped>
.strava-activity-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.125rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.error-message {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 1rem;
  color: #dc2626;
  background: #fef2f2;
  border-left: 4px solid #dc2626;
}

.loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 2rem;
  color: #6b7280;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  color: #6b7280;
  text-align: center;
}

.empty-state i {
  font-size: 2rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.activities-container {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.activity-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.activity-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.1);
}

.activity-card.selected {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
}

.activity-preview {
  display: flex;
  padding: 1rem;
  gap: 1rem;
}

.activity-info {
  flex: 1;
  min-width: 0;
}

.activity-name {
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.activity-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.stat {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #6b7280;
}

.stat i {
  width: 12px;
  text-align: center;
}

.activity-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: #9ca3af;
}

.activity-type-badge {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.gps-indicator {
  color: #10b981;
  font-size: 0.875rem;
}

.activity-map {
  width: 120px;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  background: #f8fafc;
}

.mini-map {
  width: 100%;
  height: 100%;
}

.load-more {
  padding: 1rem;
  text-align: center;
}

.selected-activity-actions {
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.no-gps-warning {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  margin-bottom: 1rem;
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 6px;
  color: #92400e;
  font-size: 0.875rem;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.75rem;
}

.btn-load-more {
  background: #f97316;
  color: white;
  border: none;
}

.btn-load-more:hover:not(:disabled) {
  background: #ea580c;
}

.btn-load-more:disabled {
  background: #fb923c;
  opacity: 0.7;
}
</style>
