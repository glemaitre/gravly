<template>
  <div v-if="isVisible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div v-if="activity" class="modal-body">
        <!-- Activity Header -->
        <div class="activity-header">
          <div class="activity-info">
            <h2 class="activity-name">{{ activity.name }}</h2>
            <div class="activity-start-time">
              {{ formatDateTime(activity.start_date_local) }}
            </div>
          </div>

          <!-- Import Actions -->
          <div class="modal-actions">
            <button
              @click="importActivity"
              :disabled="isImporting || !activity.start_latlng"
              class="btn btn-primary"
            >
              <i v-if="isImporting" class="fa-solid fa-spinner fa-spin"></i>
              <i v-else class="fa-solid fa-download"></i>
              Import
            </button>

            <button @click="closeModal" class="btn btn-secondary">
              {{ t('common.cancel') }}
            </button>
          </div>
        </div>

        <!-- Map Preview -->
        <div v-if="activity.start_latlng" class="map-section">
          <h4 class="section-title">
            <i class="fa-solid fa-map-location-dot"></i>
            {{ t('strava.routePreview') }}
          </h4>
          <div ref="mapContainer" class="activity-map"></div>
        </div>

        <!-- Activity Stats Grid -->
        <div class="stats-section">
          <h4 class="section-title">
            <i class="fa-solid fa-chart-line"></i>
            {{ t('strava.activityStats') }}
          </h4>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon">
                <i class="fa-solid fa-route"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ formatDistance(activity.distance) }}</div>
                <div class="stat-label">{{ t('strava.distance') }}</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">
                <i class="fa-solid fa-clock"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ formatDuration(activity.moving_time) }}</div>
                <div class="stat-label">{{ t('strava.movingTime') }}</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">
                <i class="fa-solid fa-mountain"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">
                  {{ formatElevation(activity.total_elevation_gain) }}
                </div>
                <div class="stat-label">{{ t('strava.elevationGain') }}</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">
                <i class="fa-solid fa-gauge"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ formatSpeed(activity.average_speed) }}</div>
                <div class="stat-label">{{ t('strava.averageSpeed') }}</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">
                <i class="fa-solid fa-tachometer-alt"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ formatSpeed(activity.max_speed) }}</div>
                <div class="stat-label">{{ t('strava.maxSpeed') }}</div>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">
                <i class="fa-solid fa-heart"></i>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ activity.average_heartrate || 'N/A' }}</div>
                <div class="stat-label">{{ t('strava.avgHeartrate') }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- GPS Warning -->
        <div v-if="!activity.start_latlng" class="gps-warning">
          <i class="fa-solid fa-exclamation-triangle"></i>
          <p>{{ t('strava.noGpsDataWarning') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import L from 'leaflet'
import type { StravaActivity } from '../composables/useStravaApi'

const { t, locale } = useI18n()

const props = defineProps<{
  isVisible: boolean
  activity: StravaActivity | null
  isImporting: boolean
}>()

const emit = defineEmits<{
  close: []
  import: [activity: StravaActivity]
}>()

const mapContainer = ref<HTMLElement | null>(null)
const map = ref<any>(null)

// Helper functions
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

const formatSpeed = (speed: number): string => {
  return `${(speed * 3.6).toFixed(1)} km/h`
}

const formatDateTime = (dateString: string): string => {
  const date = new Date(dateString)

  if (locale.value === 'fr') {
    return date.toLocaleString('fr-FR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    })
  } else {
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    })
  }
}

const getActivityTypeIcon = (type: string): string => {
  switch (type) {
    case 'Ride':
      return 'fa-solid fa-bicycle'
    case 'VirtualRide':
      return 'fa-solid fa-bicycle'
    case 'EBikeRide':
      return 'fa-solid fa-bicycle'
    case 'Run':
      return 'fa-solid fa-running'
    case 'Walk':
      return 'fa-solid fa-walking'
    default:
      return 'fa-solid fa-dumbbell'
  }
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

// Map functions
const createMap = async () => {
  if (!mapContainer.value || !props.activity?.start_latlng) return

  await nextTick()

  // Destroy existing map
  if (map.value) {
    map.value.remove()
  }

  try {
    map.value = L.map(mapContainer.value, {
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
    L.tileLayer(
      `https://{s}.tile.thunderforest.com/cycle/{z}/{x}/{y}.png?apikey=${apiKey}`,
      {
        attribution:
          'Maps © <a href="https://www.thunderforest.com/">Thunderforest</a>, Data © <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      }
    ).addTo(map.value)

    // Create polyline from summary polyline if available
    if (props.activity.map && props.activity.map.summary_polyline) {
      try {
        // Decode the polyline to get coordinates
        const coordinates = decodePolyline(props.activity.map.summary_polyline)

        if (coordinates.length > 0) {
          // For the detailed modal, we can use more points (up to 200)
          const subsampledCoords = subsampleCoordinates(coordinates, 200)

          // Create polyline with better styling for the modal
          const polyline = L.polyline(subsampledCoords, {
            color: '#f97316',
            weight: 4,
            opacity: 0.9,
            lineCap: 'round',
            lineJoin: 'round'
          }).addTo(map.value)

          // Fit map to polyline bounds
          map.value.fitBounds(polyline.getBounds(), { padding: [20, 20] })

          // Add start marker
          L.circleMarker(coordinates[0], {
            radius: 6,
            fillColor: '#10b981',
            color: '#ffffff',
            weight: 3,
            opacity: 1,
            fillOpacity: 0.9
          })
            .addTo(map.value)
            .bindPopup(t('strava.startPoint'))

          // Add end marker
          if (coordinates.length > 1) {
            L.circleMarker(coordinates[coordinates.length - 1], {
              radius: 6,
              fillColor: '#ef4444',
              color: '#ffffff',
              weight: 3,
              opacity: 1,
              fillOpacity: 0.9
            })
              .addTo(map.value)
              .bindPopup(t('strava.endPoint'))
          }
        }
      } catch (err) {
        console.warn('Failed to decode activity polyline:', err)
        // Fallback to start/end coordinates
        if (props.activity.start_latlng && props.activity.end_latlng) {
          const bounds = L.latLngBounds(
            props.activity.start_latlng,
            props.activity.end_latlng
          )
          map.value.fitBounds(bounds, { padding: [10, 10] })
        } else if (props.activity.start_latlng) {
          map.value.setView(props.activity.start_latlng, 13)
        }
      }
    } else if (props.activity.start_latlng && props.activity.end_latlng) {
      // Fallback: just show start and end points
      const bounds = L.latLngBounds(
        props.activity.start_latlng,
        props.activity.end_latlng
      )
      map.value.fitBounds(bounds, { padding: [10, 10] })

      L.marker(props.activity.start_latlng)
        .addTo(map.value)
        .bindPopup(t('strava.startPoint'))

      L.marker(props.activity.end_latlng)
        .addTo(map.value)
        .bindPopup(t('strava.endPoint'))
    } else if (props.activity.start_latlng) {
      map.value.setView(props.activity.start_latlng, 13)
      L.marker(props.activity.start_latlng)
        .addTo(map.value)
        .bindPopup(t('strava.startPoint'))
    }
  } catch (err) {
    console.error('Failed to create map:', err)
  }
}

const destroyMap = () => {
  if (map.value) {
    map.value.remove()
    map.value = null
  }
}

// Event handlers
const closeModal = () => {
  emit('close')
}

const importActivity = () => {
  if (props.activity) {
    emit('import', props.activity)
  }
}

// Watchers
watch(
  () => props.isVisible,
  (newValue) => {
    if (newValue && props.activity) {
      nextTick(() => {
        createMap()
      })
    } else {
      destroyMap()
    }
  }
)

watch(
  () => props.activity,
  () => {
    if (props.isVisible && props.activity) {
      nextTick(() => {
        createMap()
      })
    }
  }
)

onUnmounted(() => {
  destroyMap()
})

// Expose methods for testing
defineExpose({
  formatDistance,
  formatDuration,
  formatElevation,
  formatSpeed,
  formatDateTime,
  getActivityTypeIcon,
  decodePolyline,
  subsampleCoordinates,
  createMap
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 800px;
  height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.modal-body {
  padding: 24px;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
}

.activity-info {
  flex: 1;
}

.activity-name {
  margin: 0 0 4px 0;
  font-size: 1.4rem;
  font-weight: 700;
  color: #1f2937;
}

.activity-start-time {
  font-size: 0.9rem;
  color: #6b7280;
  font-weight: 500;
}

.stats-section {
  margin-bottom: 32px;
}

.section-title {
  margin: 0 0 16px 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title i {
  color: #f97316;
  font-size: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.stat-icon {
  width: 36px;
  height: 36px;
  background: #f97316;
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

.map-section {
  margin-bottom: 32px;
}

.activity-map {
  height: 300px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.modal-actions {
  display: flex;
  flex-direction: row;
  gap: 8px;
  align-items: flex-start;
}

.btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background: #f97316;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #ea580c;
}

.btn-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-secondary {
  background: #6b7280;
  color: white;
}

.btn-secondary:hover {
  background: #4b5563;
}

.gps-warning {
  background: #fef3c7;
  border: 1px solid #fde68a;
  color: #92400e;
  padding: 16px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.gps-warning i {
  font-size: 1rem;
}

.gps-warning p {
  margin: 0;
  font-weight: 500;
}

@media (max-width: 768px) {
  .modal-content {
    margin: 10px;
    height: 80vh;
  }

  .modal-header {
    padding: 16px 20px;
  }

  .modal-body {
    padding: 20px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .activity-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .modal-actions {
    align-items: flex-start;
    width: auto;
  }
}
</style>
