<template>
  <div v-if="isVisible" class="modal-overlay" @click="closeModal">
    <div class="modal-content" @click.stop>
      <div class="modal-header">
        <h3>{{ t('strava.activityDetails') }}</h3>
        <button @click="closeModal" class="close-btn" :title="t('common.close')">
          <i class="fa-solid fa-times"></i>
        </button>
      </div>

      <div v-if="activity" class="modal-body">
        <!-- Activity Header -->
        <div class="activity-header">
          <h2 class="activity-name">{{ activity.name }}</h2>
          <div class="activity-type-badge">
            <i :class="getActivityTypeIcon(activity.type)"></i>
            <span>{{ activity.type }}</span>
          </div>
        </div>

        <!-- Activity Stats Grid -->
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

        <!-- Activity Details -->
        <div class="activity-details">
          <div class="detail-section">
            <h4>{{ t('strava.activityInfo') }}</h4>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">{{ t('strava.startTime') }}:</span>
                <span class="detail-value">{{
                  formatDateTime(activity.start_date_local)
                }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">{{ t('strava.totalTime') }}:</span>
                <span class="detail-value">{{
                  formatDuration(activity.elapsed_time)
                }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">{{ t('strava.kudos') }}:</span>
                <span class="detail-value">{{ activity.kudos_count }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">{{ t('strava.comments') }}:</span>
                <span class="detail-value">{{ activity.comment_count }}</span>
              </div>
            </div>
          </div>

          <!-- GPS Status -->
          <div class="detail-section">
            <h4>{{ t('strava.gpsStatus') }}</h4>
            <div
              class="gps-status"
              :class="{
                'has-gps': activity.start_latlng,
                'no-gps': !activity.start_latlng
              }"
            >
              <i
                :class="
                  activity.start_latlng
                    ? 'fa-solid fa-location-dot'
                    : 'fa-solid fa-exclamation-triangle'
                "
              ></i>
              <span>{{
                activity.start_latlng
                  ? t('strava.gpsDataAvailable')
                  : t('strava.noGpsData')
              }}</span>
            </div>
          </div>
        </div>

        <!-- Map Preview -->
        <div v-if="activity.start_latlng" class="map-section">
          <h4>{{ t('strava.routePreview') }}</h4>
          <div ref="mapContainer" class="activity-map"></div>
        </div>

        <!-- Import Actions -->
        <div class="modal-actions">
          <button
            @click="importActivity"
            :disabled="isImporting || !activity.start_latlng"
            class="btn btn-primary btn-lg"
          >
            <i v-if="isImporting" class="fa-solid fa-spinner fa-spin"></i>
            <i v-else class="fa-solid fa-download"></i>
            {{ t('strava.importActivity') }}
          </button>

          <button @click="closeModal" class="btn btn-secondary btn-lg">
            {{ t('common.cancel') }}
          </button>
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

const { t } = useI18n()

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
  return date.toLocaleString()
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

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map.value)

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
            color: '#3b82f6',
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
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: #1f2937;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  color: #6b7280;
  cursor: pointer;
  padding: 8px;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
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

.activity-name {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: #1f2937;
  flex: 1;
}

.activity-type-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #3b82f6;
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.9rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.stat-icon {
  width: 40px;
  height: 40px;
  background: #3b82f6;
  color: white;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #1f2937;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 0.875rem;
  color: #6b7280;
  font-weight: 500;
}

.activity-details {
  margin-bottom: 32px;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f1f5f9;
}

.detail-label {
  font-weight: 500;
  color: #6b7280;
}

.detail-value {
  font-weight: 600;
  color: #1f2937;
}

.gps-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  font-weight: 500;
}

.gps-status.has-gps {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #bbf7d0;
}

.gps-status.no-gps {
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
}

.map-section {
  margin-bottom: 32px;
}

.map-section h4 {
  margin: 0 0 12px 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: #1f2937;
}

.activity-map {
  height: 300px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 16px;
}

.btn {
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-lg {
  padding: 16px 32px;
  font-size: 1.1rem;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
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
  font-size: 1.2rem;
}

.gps-warning p {
  margin: 0;
  font-weight: 500;
}

@media (max-width: 768px) {
  .modal-content {
    margin: 10px;
    max-height: 95vh;
  }

  .modal-header {
    padding: 16px 20px;
  }

  .modal-body {
    padding: 20px;
  }

  .activity-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .modal-actions {
    flex-direction: column;
  }
}
</style>
